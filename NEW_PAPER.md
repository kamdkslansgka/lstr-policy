# 新论文网站快速流程

这个仓库现在可以作为模板仓库使用。每次新论文建站，建议生成一个新的干净目录，不要直接覆盖当前 RCAF 项目。

## 1. 生成新论文站点

在当前仓库根目录运行：

```bash
npm run new-paper -- ../my-new-paper-site --title "Your Paper Title" --repo my-new-paper-site
```

常用参数：

```bash
npm run new-paper -- ../my-new-paper-site \
  --title "Your Paper Title" \
  --repo my-new-paper-site \
  --author "Anonymous" \
  --institution "Anonymous" \
  --conference "Conference Name"
```

`--repo` 要和 GitHub 仓库名一致。比如仓库是 `new-policy`，页面地址通常会是：

```text
https://kamdkslansgka.github.io/new-policy/
```

## 2. 本地预览

```bash
cd ../my-new-paper-site
npm install
npm run dev
```

打开终端里显示的本地地址即可预览。

## 3. 写页面内容

主要改这些地方：

- `src/paper.mdx`：论文网站正文、标题、作者、链接、摘要、图表说明。
- `bibliography.bib`：参考文献 BibTeX。
- `public/image/`：放图片、主图、结果图。
- `public/videos/`：放视频。

如果 `--repo` 是 `my-new-paper-site`，公共资源路径写成：

```mdx
<img src="/my-new-paper-site/image/teaser.svg" alt="Project teaser" />
<video
  src="/my-new-paper-site/videos/demo.mp4"
  autoPlay
  loop
  muted
  playsInline
/>
```

## 4. 发布到 GitHub Pages

1. 在 GitHub 新建同名仓库，例如 `my-new-paper-site`。
2. 把生成的新目录提交并推到 `main` 分支。
3. 在仓库 `Settings -> Pages` 中，把 Source 设为 `GitHub Actions`。
4. 之后每次 push，`.github/workflows/astro.yml` 会自动构建并部署。

## 5. 推荐工作方式

先把论文 LaTeX 源码、图片和实验视频放进新目录，再让 AI 帮你把 `src/paper.mdx` 填成项目页。页面初稿稳定后，再精修摘要、图注、视频布局和链接按钮。
