from django.http import HttpResponse, HttpResponseBadRequest
from django.db import IntegrityError

from wh_former.models import RFID_setting, RFID_read_log, Basket_master_data
from datetime import datetime
import threading
import socket
import time
from collections import defaultdict
import queue
from concurrent.futures import ThreadPoolExecutor


import multiprocessing as mp
import ctypes
import os
import re



reader_instances = {}
active_pid_per_ip = {}
uhf_api = ctypes.CDLL(os.path.join(os.path.abspath(os.path.abspath(".")), "wh_former", "utils", "rfid", "rfid.dll"))


CELL_INVALID = 0
CELL_CONNECT_ID = 1
CELL_CONNECT_IP = 2
CELL_UHF_PC = 3
CELL_UHF_RSSI = 4
CELL_UHF_ANTENNA = 5
CELL_UHF_EPC = 6
CELL_UHF_TID = 7
CELL_UHF_USER = 8
CELL_UHF_RESERVE = 9
CELL_BARCODE = 10
CELL_UHF_SENSOR = 11
CELL_INPUT = 12
CELL_KEY_CODE = 13
CELL_UHF_PHASE = 14


uhf_api.ComOpen.argtypes = [ctypes.c_int]
uhf_api.ComOpen.restype = ctypes.c_int
uhf_api.UHFInventory.restype = ctypes.c_int
uhf_api.UHFGetTagData.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
uhf_api.UHFGetTagData.restype = ctypes.c_int
uhf_api.UHFStopGet.restype = ctypes.c_int

_threads = {}

class UHFTAGInfo:
    def __init__(self):
        self.epc = None
        self.pc = None
        self.tid = None
        self.user = None
        self.rssi = None
        self.ant = None
        self.phase = None


class TagInfo:
    def __init__(self):
        self.err_code = None
        self.id = None
        self.uhf_tag_info = UHFTAGInfo()
        self.raw_data = None


class UHFReader:
    def __init__(self, client_ip, ip, port, username, pid):
        self.client = client_ip
        self.ip = ip
        self.port = port
        self.is_running = False
        self.username = username
        self.pid = pid
        self.scan_times = int(int(datetime.now().strftime("%Y%m%d%H%M%S"))/10)
        self.epc_seen = {}
        self.epc_counter = defaultdict(int)
        self.EPC_CONFIRM_THRESHOLD = 1
        self.EPC_TIMEOUT = 2
        self.lock = threading.Lock()
        self.epc_processed = set()

        self.epc_queue = queue.Queue(maxsize=2000)
        self.db_queue = queue.Queue(maxsize=500)

        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="UHF")

        # Log file disabled
        # base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        # self.log_filename = os.path.join(base_dir, f"epc_log_{self.ip.replace('.', '_')}.txt")
        # print(f"Log file path: {self.log_filename}")

        self._basket_cache = set()
        self._cache_last_update = 0
        self._cache_ttl = 300
        self._update_basket_cache()

        # Disable log file creation
        # with open(self.log_filename, "w", encoding="utf-8") as f:
        #     f.write("")

    def _update_basket_cache(self):
        try:
            self._basket_cache = set(Basket_master_data.objects.values_list('basket_no', flat=True))
            self._cache_last_update = time.time()
        except Exception as e:
            print(f"Error updating basket cache: {e}")

    def _is_valid_basket(self, basket_no):
        now = time.time()
        if now - self._cache_last_update > self._cache_ttl:
            self._update_basket_cache()
        return basket_no in self._basket_cache

    def get_tag_data(self):
        tag_info = TagInfo()
        tag_temp_data = (ctypes.c_ubyte * 150)()
        result = uhf_api.UHFGetTagData(tag_temp_data, len(tag_temp_data))
        tag_info.err_code = result

        if result <= 0:
            return None

        tag_info.raw_data = bytes(tag_temp_data[:result])
        index = 0
        uhf_info = UHFTAGInfo()

        while index < result:
            if index + 2 > result:
                break
            data_type = tag_temp_data[index]
            index += 1
            data_length = tag_temp_data[index]
            index += 1
            if index + data_length > result:
                break
            cut_data = tag_temp_data[index:index + data_length]
            data = bytes(cut_data)
            index += data_length

            if data_type == 1:
                uhf_info.epc = data.hex().upper()
            elif data_type == CELL_UHF_PC:
                uhf_info.pc = data.hex().upper()
            elif data_type == CELL_UHF_TID:
                uhf_info.tid = data[:12].hex().upper()
                if len(data) > 12:
                    uhf_info.user = data[12:].hex().upper()
            elif data_type == CELL_UHF_RSSI and len(data) >= 2:
                rssi_temp = int.from_bytes(data[:2], byteorder='big', signed=True)
                uhf_info.rssi = str(rssi_temp / 10.0)
            elif data_type == CELL_UHF_ANTENNA and len(data) >= 1:
                uhf_info.ant = str(data[0])
            elif data_type == CELL_CONNECT_ID and len(data) >= 1:
                tag_info.id = data[0]
            elif data_type == CELL_UHF_PHASE and len(data) >= 2:
                uhf_info.phase = int.from_bytes(data[:2], byteorder='big')

        tag_info.uhf_tag_info = uhf_info

        if uhf_info.ant is None:
            return None

        if '3002' in str(tag_info.uhf_tag_info.epc):
            print(f"{self.ip} -> {tag_info.uhf_tag_info.epc}")
        return tag_info


    def read_epc(self):
        global active_pid_per_ip
        scan_times = self.scan_times
        empty_read_count = 0
        last_cleanup = time.time()

        while self.is_running:
            try:
                tag_info = self.get_tag_data()

                if tag_info:
                    empty_read_count = 0
                    epc = tag_info.uhf_tag_info.epc
                    if epc:
                        epc = epc.strip().upper()
                        # Disable log file writing
                        # with open(log_filename, "a", encoding="utf-8") as f:
                        #     f.write(f"{epc}")
                        if len(epc) > 4:
                            epc = epc[4:]
                            # print(epc)
                        if active_pid_per_ip.get(self.ip) != self.pid:
                            continue
                        if epc in self.epc_processed:
                            continue

                        now = time.time()
                        self.epc_seen[epc] = now
                        self.epc_counter[epc] += 1

                        if self.epc_counter[epc] >= self.EPC_CONFIRM_THRESHOLD:
                            self.epc_counter[epc] = 0

                            if self._is_valid_basket(epc):
                                existing = RFID_read_log.objects.filter(
                                    rfid_reader_ip=self.ip,
                                    basket_no=epc,
                                    pid=self.pid,
                                    is_passed=False
                                ).exists()
                                print(f"self.ip = {self.ip} -||- epc = {epc}")

                                if not existing:
                                    try:
                                        RFID_read_log.objects.create(
                                            rfid_reader_ip=self.ip,
                                            basket_no=epc,
                                            pid=self.pid,
                                            scan_times=scan_times,
                                            create_by=self.username
                                        )
                                    except IntegrityError:
                                        pass

                            self.epc_processed.add(epc)
                else:
                    empty_read_count += 1
                    if empty_read_count > 10:
                        time.sleep(0.001)

                now = time.time()
                if now - last_cleanup > 1.0:
                    self.epc_seen = {k: v for k, v in self.epc_seen.items() if now - v < self.EPC_TIMEOUT}
                    self.epc_counter = defaultdict(int, {k: v for k, v in self.epc_counter.items() if k in self.epc_seen})
                    last_cleanup = now

            except Exception as e:
                print("RFID read error:", e)
                time.sleep(0.005)

    def _db_writer(self):
        BATCH_SIZE = 50
        buffer = []
        while True:
            try:
                epc, scan_times = self.epc_queue.get()
                buffer.append((epc, scan_times))

                if len(buffer) >= BATCH_SIZE or self.epc_queue.empty():
                    epcs = [epc for epc, _ in buffer]

                    existing = set(RFID_read_log.objects.filter(
                        rfid_reader_ip=self.ip, basket_no__in=epcs, pid=self.pid, is_passed=False
                    ).values_list('basket_no', flat=True))

                    valid_baskets = set(Basket_master_data.objects.filter(basket_no__in=epcs).values_list('basket_no', flat=True))
                    to_create = []
                    for epc, scan_times in buffer:
                        if epc not in existing and epc in valid_baskets:
                            to_create.append(RFID_read_log(
                                rfid_reader_ip=RFID_setting.objects.get(rfid_reader_ip=self.ip),
                                basket_no=epc,
                                pid=self.pid,
                                scan_times=scan_times,
                                create_by=self.username
                            ))
                    if to_create:
                        for record in to_create:
                            try:
                                record.save()
                            except IntegrityError:
                                pass
                    buffer.clear()
            except Exception as e:
                print("DB write error:", e)
            time.sleep(1)

    def _write_batch_to_db(self, buffer):
        try:
            epcs = [epc for epc, _ in buffer]

            existing = set(RFID_read_log.objects.filter(
                rfid_reader_ip=self.ip,
                basket_no__in=epcs,
                pid=self.pid,
                is_passed=False
            ).values_list('basket_no', flat=True))

            to_create = []
            controller_obj = RFID_setting.objects.get(rfid_reader_ip=self.ip)

            for epc, scan_times in buffer:
                if epc not in existing:
                    to_create.append(RFID_read_log(
                        rfid_reader_ip=controller_obj,
                        basket_no=epc,
                        pid=self.pid,
                        scan_times=scan_times,
                        create_by=self.username
                    ))

            if to_create:
                for record in to_create:
                    try:
                        record.save()
                    except IntegrityError:
                        pass

        except Exception as e:
            print(f"Batch DB write error: {e}")



def rfid_test_connection(ip: str, port: int) -> bool:
    if not ip or not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip.strip()):
        return False

    try:
        uhf_api.TCPConnect.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        uhf_api.TCPConnect.restype  = ctypes.c_int

        b_ip = ctypes.create_string_buffer(ip.strip().encode("utf-8"))
        result = uhf_api.TCPConnect(b_ip, ctypes.c_uint(port))
        print(f"TCPConnect({ip}, {port}) -> {result}")
        return result == 0

    except Exception as e:
        print(f"TCP connect error: {e}")
        return False



def tcp_connect(ip: str, port: int) -> bool:
    if not ip or not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip.strip()):
        print("Invalid IP format")
        return False

    try:
        uhf_api.TCPConnect.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        uhf_api.TCPConnect.restype  = ctypes.c_int

        b_ip = ctypes.create_string_buffer(ip.strip().encode("utf-8"))
        result = uhf_api.TCPConnect(b_ip, ctypes.c_uint(port))
        print(f"TCPConnect({ip}, {port}) -> {result}")
        return result == 0

    except Exception as e:
        print(f"TCP connect error: {e}")
        return False



def tcp_disconnect():
    try:
        if not hasattr(uhf_api, "TCPDisconnect"):
            print("TCPDisconnect not found in DLL")
            return False

        uhf_api.TCPDisconnect.restype = None
        uhf_api.TCPDisconnect.argtypes = []
        uhf_api.TCPDisconnect()

        print("TCP connection closed successfully.")
        return True

    except Exception as e:
        print(f"Error during TCP disconnect: {e}")
        return False




def rfid_start_stop(request, id, username, pid):
    global reader_instances

    if request.method != "POST":
        return False
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)
        client = setting.client_device_ip
        ip = setting.rfid_reader_ip
        port = setting.rfid_reader_port

        key = (id, pid)
        reader_data = reader_instances.get(key)
        reader = reader_data[0] if reader_data else None

        if reader is None or not reader.is_running:
            if not tcp_connect(ip, port):
                return False
            inventory_result = uhf_api.UHFInventory()
            if inventory_result != 0:
                return False

            reader = UHFReader(client, ip, port, username, pid)
            reader.is_running = True

            t = threading.Thread(target=reader.read_epc, daemon=True)
            t.start()

            reader_instances[key] = (reader, t)
            return True
        else:
            stop_result = uhf_api.UHFStopGet()
            if stop_result == 0:
                reader.is_running = False
                reader_instances.pop(key, None)
                return True
            else:
                return False
    except RFID_setting.DoesNotExist:
        return False



def start_reader(request, id, username, pid):
    global reader_instances

    if request.method != "POST":
        return False
    try:
        setting = RFID_setting.objects.get(id=id, is_control=True)
        client = setting.client_device_ip
        ip = setting.rfid_reader_ip
        port = setting.rfid_reader_port

        reader_data = reader_instances.get(id)
        reader, thread = reader_data if reader_data else (None, None)

        if reader and reader.is_running:
            if reader.pid != pid:
                uhf_api.UHFStopGet()
                reader.is_running = False
                thread.join(timeout=1)
                reader_instances.pop(id, None)
            else:
                return False

        active_pid_per_ip[ip] = pid

        if not tcp_connect(ip, port):
            return False

        if uhf_api.UHFInventory() != 0:
            return False

        reader = UHFReader(client, ip, port, username, pid)
        reader.is_running = True
        t = threading.Thread(target=reader.read_epc, daemon=True)
        t.start()

        reader_instances[id] = (reader, t)
        return True
    except RFID_setting.DoesNotExist:
        return False


def stop_reader(request, id):
    global reader_instances

    if request.method != "POST":
        return False

    try:
        reader_data = reader_instances.get(id)
        if not reader_data:
            return True

        reader, thread = reader_data
        if not reader.is_running:
            reader_instances.pop(id, None)
            return True

        stop_result = uhf_api.UHFStopGet()
        if stop_result == 0:
            reader.is_running = False
            try:
                thread.join(timeout=0.5)
            except Exception:
                pass
            reader_instances.pop(id, None)
            active_pid_per_ip.pop(reader.ip, None)
            tcp_disconnect()

            return True

        reader.is_running = False
        try:
            thread.join(timeout=0.5)
        except Exception:
            pass
        reader_instances.pop(id, None)
        active_pid_per_ip.pop(reader.ip, None)
        return True
    except Exception as e:
        print("Stop reader error:", e)
        return True






