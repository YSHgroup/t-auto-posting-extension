import { existsSync, mkdirSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'

const webRoot = resolve(new URL('..', import.meta.url).pathname)
const dist = resolve(webRoot, 'dist')
const output = resolve(webRoot, 'telegram-auto-bot-extension.zip')
if (!existsSync(dist)) {
  console.error('dist does not exist. Run npm run build first.')
  process.exit(1)
}
mkdirSync(resolve(webRoot), { recursive: true })
execFileSync('zip', ['-qr', output, '.'], { cwd: dist, stdio: 'inherit' })
console.log(`Extension package created: ${output}`)
