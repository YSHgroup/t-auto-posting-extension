import { existsSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(new URL('../dist', import.meta.url).pathname)
const required = ['manifest.json', 'index.html', 'background.js']
const missing = required.filter((file) => !existsSync(resolve(root, file)))
if (missing.length > 0) {
  console.error(`Extension build is missing: ${missing.join(', ')}`)
  process.exit(1)
}
const manifest = JSON.parse(readFileSync(resolve(root, 'manifest.json'), 'utf8'))
if (manifest.manifest_version !== 3 || !manifest.side_panel?.default_path) {
  console.error('dist/manifest.json is not a valid Manifest V3 side-panel extension')
  process.exit(1)
}
console.log(`Chrome extension ready: ${root}`)
console.log('Load this folder from chrome://extensions using Load unpacked.')
