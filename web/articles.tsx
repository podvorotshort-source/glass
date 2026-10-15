// Стеклянные папки со статьями на главной.
// Данные кладёт в страницу tools/build_articles.py: <script id="articles-data">.
import * as React from "react"
import { createRoot } from "react-dom/client"
import GlassFolder, { type FolderFile } from "./glass-folder-cards"

type Folder = {
  label: string
  meta: string
  image?: string
  files: FolderFile[]
}

// ширина папки под сетку: 4 в ряд на широком экране, 2 на планшете, 1 на телефоне
const widthFor = (vw: number) => (vw < 560 ? Math.min(320, vw - 48) : vw < 1180 ? 290 : 300)

function Folders({ folders }: { folders: Folder[] }) {
  const [width, setWidth] = React.useState(() => widthFor(window.innerWidth))
  React.useEffect(() => {
    const onResize = () => setWidth(widthFor(window.innerWidth))
    window.addEventListener("resize", onResize)
    return () => window.removeEventListener("resize", onResize)
  }, [])

  return (
    <>
      {folders.map((f, i) => (
        <GlassFolder
          key={f.label}
          label={f.label}
          meta={f.meta}
          tone="light"
          image={f.image}
          art={f.image ? undefined : "none"}
          files={f.files}
          action="none"
          width={width}
          appearDelay={(i % 4) * 120}
        />
      ))}
    </>
  )
}

const mount = document.getElementById("articles-folders")
const data = document.getElementById("articles-data")
if (mount && data) {
  const folders = JSON.parse(data.textContent || "[]") as Folder[]
  createRoot(mount).render(<Folders folders={folders} />)
}
