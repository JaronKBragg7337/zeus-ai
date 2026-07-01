import { build } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

async function main() {
  try {
    await build({
      plugins: [react(), tailwindcss()],
      build: {
        outDir: 'dist',
        emptyOutDir: true,
      },
    })
    console.log('Build completed successfully!')
  } catch (e) {
    console.error('Build failed:', e)
    process.exit(1)
  }
}

main()
