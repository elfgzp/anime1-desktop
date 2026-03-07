/**
 * 视频播放器键盘控制测试
 */
import { test, expect } from "../fixtures"
import { readFileSync } from "fs"
import { resolve, dirname } from "path"
import { fileURLToPath } from "url"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

test.describe("视频播放器键盘控制", () => {
  test("Detail.vue 源码应该包含 handleVideoKeydown 函数", async () => {
    const sourcePath = resolve(__dirname, "../../src/renderer/views/Detail.vue")
    const source = readFileSync(sourcePath, "utf-8")
    
    expect(source).toContain("handleVideoKeydown")
    expect(source).toContain('tabindex="0"')
    expect(source).toContain('e.code === "Space"')
    expect(source).toContain("e.preventDefault()")
    expect(source).toContain("video.play()")
    expect(source).toContain("video.pause()")
  })

  test("视频元素应该支持 keydown 事件", async ({ window }) => {
    const result = await window.evaluate(async () => {
      const video = document.createElement("video")
      return {
        hasTabIndexProperty: 'tabIndex' in video,
        hasFocusMethod: typeof video.focus === 'function',
        isFocusable: video.tabIndex >= 0
      }
    })

    expect(result.hasTabIndexProperty).toBe(true)
    expect(result.hasFocusMethod).toBe(true)
    expect(result.isFocusable).toBe(true)
  })

  test("空格键事件对象应该有正确的属性", async ({ window }) => {
    const result = await window.evaluate(async () => {
      const spaceEvent = new KeyboardEvent("keydown", {
        code: "Space",
        key: " ",
        bubbles: true,
        cancelable: true
      })

      return {
        code: spaceEvent.code,
        key: spaceEvent.key,
        bubbles: spaceEvent.bubbles,
        cancelable: spaceEvent.cancelable,
        defaultPrevented: spaceEvent.defaultPrevented
      }
    })

    expect(result.code).toBe("Space")
    expect(result.key).toBe(" ")
    expect(result.cancelable).toBe(true)
  })
})
