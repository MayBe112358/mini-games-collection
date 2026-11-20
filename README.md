# 小游戏合集

当前根目录是小游戏合集入口页，已接入：

- 三羊开泰：`./san-yang-kai-tai/index.html`
- 跳一跳：`./tiaoyitiao/index.html`
- 一色一牛：`./yi-se-yi-niu/index.html`
- 黑白接力：`./hei-bai-jie-li/index.html`（关卡求解器与生成器在 `./hei-bai-jie-li/tools/`）

## 新增小游戏

1. 把新项目文件夹放到当前目录，例如 `2048/`。文件夹名只用英文、拼音、数字和连字符，不要用中文，这样线上地址里不会出现中文。
2. 确认项目入口为 `index.html`，或在配置里写正确入口路径。
3. 在 `games.js` 的 `games` 数组里追加：

```js
{
  title: "2048",
  subtitle: "数字合成",
  description: "滑动方块合成更高数字。",
  category: "益智",
  tags: ["HTML", "键盘", "移动端"],
  version: "HTML",
  emoji: "🔢",
  localUrl: "./2048/index.html",
  liveUrl: "https://example.com/2048/",
  thumbnail: "./assets/thumbs/2048.png"
}
```

`thumbnail` 可选；没有图片或图片加载失败时，页面会自动显示 emoji 兜底。
