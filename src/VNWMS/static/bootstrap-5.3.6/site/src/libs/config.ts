import fs from 'node:fs'
import yaml from 'js-yaml'
import { z } from 'zod'
import { zPrefixedVersionSemver, zVersionMajorMinor, zVersionSemver } from './validation'

// The configs schema used to validate the configs file content and ensure all values required by the site are valid.
const configSchema = z.object({
  algolia: z.object({
    api_key: z.string(),
    app_id: z.string(),
    index_name: z.string()
  }),
  analytics: z.object({
    fathom_site: z.string()
  }),
  anchors: z.object({
    min: z.number(),
    max: z.number()
  }),
  authors: z.string(),
  baseURL: z.string().url(),
  blog: z.string().url(),
  cdn: z.object({
    css: z.string().url(),
    css_rtl: z.string().url(),
    css_hash: z.string(),
    css_rtl_hash: z.string(),
    js: z.string().url(),
    js_hash: z.string(),
    js_bundle: z.string().url(),
    js_bundle_hash: z.string(),
    popper: z.string().url(),
    popper_esm: z.string().url(),
    popper_hash: z.string()
  }),
  current_version: zVersionSemver,
  current_ruby_version: zVersionSemver,
  description: z.string(),
  docs_version: zVersionMajorMinor,
  docsDir: z.string(),
  download: z.object({
    dist: z.string().url(),
    dist_examples: z.string().url(),
    source: z.string().url()
  }),
  github_org: z.string().url(),
  icons: z.string().url(),
  opencollective: z.string().url(),
  repo: z.string().url(),
  rfs_version: zPrefixedVersionSemver,
  subtitle: z.string(),
  swag: z.string().url(),
  themes: z.string().url(),
  title: z.string(),
  toc: z.object({
    min: z.number(),
    max: z.number()
  }),
  x: z.string()
})

let config: Config | undefined

// A helper to get the configs loaded fom the `configs.yml` file. If the configs does not match the `configSchema`, an
// error is thrown to indicate that the configs file is invalid and some action is required.
export function getConfig(): Config {
  if (config) {
    // Returns the configs if it has already been loaded.
    return config
  }

  try {
    // Load the configs from the `configs.yml` file.
    const rawConfig = yaml.load(fs.readFileSync('./configs.yml', 'utf8'))

    // Parse the configs using the configs schema to validate its content and get back a fully typed configs object.
    config = configSchema.parse(rawConfig)

    return config
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('The `configs.yml` file content is invalid:', error.issues)
    }

    throw new Error('Failed to load configuration from `configs.yml`', { cause: error })
  }
}

type Config = z.infer<typeof configSchema>
