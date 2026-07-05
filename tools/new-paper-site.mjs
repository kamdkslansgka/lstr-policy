#!/usr/bin/env node

import {
  cp,
  mkdir,
  readdir,
  readFile,
  stat,
  writeFile,
} from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const templateRoot = path.resolve(scriptDir, "..");

const copyEntries = [
  ".github",
  ".vscode",
  ".gitignore",
  ".prettierignore",
  "NEW_PAPER.md",
  "README.md",
  "documentation.md",
  "astro.config.ts",
  "eslint.config.ts",
  "package-lock.json",
  "package.json",
  "prettier.config.ts",
  "src/components",
  "src/lib",
  "src/pages",
  "src/styles",
  "src/types",
  "starwind.config.json",
  "tools/new-paper-site.mjs",
  "tsconfig.json",
];

const defaultSite = "https://kamdkslansgka.github.io";

function printHelp() {
  console.log(`Create a clean project-page repo for a new paper.

Usage:
  npm run new-paper -- ../my-paper-site --title "Paper Title" --repo my-paper-site

Options:
  --title        Paper title for src/paper.mdx
  --repo         GitHub repository name. Also used as Astro base path.
  --site         GitHub Pages origin. Default: ${defaultSite}
  --author       First author name. Default: Anonymous
  --institution  First author institution. Default: Anonymous
  --conference   Conference or venue line. Default: Conference Name
  --description  Link preview description. Defaults to a generic project-page description.
`);
}

function parseArgs(argv) {
  const options = {};

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === "--help" || arg === "-h") {
      options.help = true;
      continue;
    }

    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const value = argv[index + 1];

      if (!value || value.startsWith("--")) {
        throw new Error(`Missing value for --${key}`);
      }

      options[key] = value;
      index += 1;
      continue;
    }

    if (!options.target) {
      options.target = arg;
      continue;
    }

    throw new Error(`Unexpected argument: ${arg}`);
  }

  return options;
}

function cleanRepoName(input) {
  return input
    .trim()
    .replace(/^\/+|\/+$/g, "")
    .replace(/\.git$/i, "")
    .replace(/\s+/g, "-");
}

function packageNameFromRepo(repo) {
  const name = repo
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return name || "paper-project-page";
}

function yamlString(value) {
  return JSON.stringify(value ?? "");
}

function svgText(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

async function assertEmptyOrMissingDirectory(targetDir) {
  if (!existsSync(targetDir)) {
    return;
  }

  const targetStats = await stat(targetDir);
  if (!targetStats.isDirectory()) {
    throw new Error(`Target exists and is not a directory: ${targetDir}`);
  }

  const entries = await readdir(targetDir);
  if (entries.length > 0) {
    throw new Error(`Target directory is not empty: ${targetDir}`);
  }
}

async function copyTemplateFiles(targetDir) {
  for (const entry of copyEntries) {
    const source = path.join(templateRoot, entry);

    if (!existsSync(source)) {
      continue;
    }

    await cp(source, path.join(targetDir, entry), {
      recursive: true,
      preserveTimestamps: true,
    });
  }

  await mkdir(path.join(targetDir, "public", "image"), { recursive: true });
  await mkdir(path.join(targetDir, "public", "videos"), { recursive: true });
  await mkdir(path.join(targetDir, "src", "assets"), { recursive: true });

  await cp(
    path.join(templateRoot, "public", "favicon.svg"),
    path.join(targetDir, "public", "favicon.svg"),
  );
}

async function updatePackageFiles(targetDir, packageName) {
  const packageJsonPath = path.join(targetDir, "package.json");
  const packageJson = JSON.parse(await readFile(packageJsonPath, "utf8"));
  packageJson.name = packageName;
  await writeFile(packageJsonPath, `${JSON.stringify(packageJson, null, 2)}\n`);

  const lockPath = path.join(targetDir, "package-lock.json");
  if (!existsSync(lockPath)) {
    return;
  }

  const lockJson = JSON.parse(await readFile(lockPath, "utf8"));
  lockJson.name = packageName;
  if (lockJson.packages?.[""]) {
    lockJson.packages[""].name = packageName;
  }
  await writeFile(lockPath, `${JSON.stringify(lockJson, null, 2)}\n`);
}

async function updateAstroConfig(targetDir, site, repo) {
  const astroConfigPath = path.join(targetDir, "astro.config.ts");
  const config = await readFile(astroConfigPath, "utf8");
  const base = `/${repo}`;
  const updated = config
    .replace(/site:\s*["'][^"']*["']/, `site: ${JSON.stringify(site)}`)
    .replace(/base:\s*["'][^"']*["']/, `base: ${JSON.stringify(base)}`);

  await writeFile(astroConfigPath, updated);
}

async function writeStarterPaper(targetDir, options) {
  const { title, author, institution, conference, description, repo } = options;

  const paper = `---
title: ${yamlString(title)}
authors:
  - name: ${yamlString(author)}
    institution: ${yamlString(institution)}
conference: ${yamlString(conference)}
theme: device
favicon: favicon.svg
description: ${yamlString(description)}
---

import HighlightedSection from "./components/HighlightedSection.astro";
import Figure from "./components/Figure.astro";

<Figure>
  <img slot="figure" src="/${repo}/image/teaser.svg" alt="Project teaser" className="w-full rounded-lg shadow-sm border border-gray-200" />
  <Fragment slot="caption">Replace this teaser with the main figure or result from the paper.</Fragment>
</Figure>

<HighlightedSection>

## Abstract

Paste the paper abstract here.

</HighlightedSection>

## Method

Summarize the key idea in two or three short paragraphs. Focus on what changes compared with prior work and why it matters.

## Results

Add the main quantitative table, qualitative figures, and videos here.

## BibTeX

\`\`\`bibtex
@misc{yourkey2026,
  title = {${title}},
  author = {${author}},
  year = {2026}
}
\`\`\`
`;

  const teaserSvg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" role="img" aria-labelledby="title desc">
  <title id="title">Project teaser placeholder</title>
  <desc id="desc">Temporary project teaser placeholder for ${svgText(title)}</desc>
  <rect width="1200" height="630" fill="#f4f4f5"/>
  <rect x="54" y="54" width="1092" height="522" rx="28" fill="#ffffff" stroke="#d4d4d8" stroke-width="2"/>
  <path d="M126 420 C260 270 350 350 468 230 C585 112 704 275 824 190 C930 114 1026 204 1080 144" fill="none" stroke="#2563eb" stroke-width="18" stroke-linecap="round"/>
  <circle cx="260" cy="270" r="24" fill="#10b981"/>
  <circle cx="468" cy="230" r="24" fill="#f59e0b"/>
  <circle cx="824" cy="190" r="24" fill="#ef4444"/>
  <text x="96" y="510" fill="#18181b" font-family="Arial, Helvetica, sans-serif" font-size="54" font-weight="700">Project teaser</text>
  <text x="96" y="560" fill="#52525b" font-family="Arial, Helvetica, sans-serif" font-size="28">Replace public/image/teaser.svg with your main figure.</text>
</svg>
`;

  await writeFile(path.join(targetDir, "src", "paper.mdx"), paper);
  await writeFile(path.join(targetDir, "bibliography.bib"), "");
  await writeFile(
    path.join(targetDir, "public", "image", "teaser.svg"),
    teaserSvg,
  );
  await writeFile(path.join(targetDir, "public", "image", ".gitkeep"), "");
  await writeFile(path.join(targetDir, "public", "videos", ".gitkeep"), "");
  await writeFile(path.join(targetDir, "src", "assets", ".gitkeep"), "");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    printHelp();
    return;
  }

  if (!args.target) {
    printHelp();
    process.exitCode = 1;
    return;
  }

  const targetDir = path.resolve(process.cwd(), args.target);
  if (targetDir === templateRoot) {
    throw new Error(
      "Refusing to scaffold into the current template directory.",
    );
  }

  const repo = cleanRepoName(args.repo || path.basename(targetDir));
  if (!repo) {
    throw new Error(
      "Could not infer a repository name. Pass --repo explicitly.",
    );
  }

  const options = {
    title: args.title || "New Paper Title",
    repo,
    site: args.site || defaultSite,
    author: args.author || "Anonymous",
    institution: args.institution || "Anonymous",
    conference: args.conference || "Conference Name",
    description:
      args.description ||
      "Project page for a research paper, built with Astro and Tailwind.",
  };

  await assertEmptyOrMissingDirectory(targetDir);
  await mkdir(targetDir, { recursive: true });
  await copyTemplateFiles(targetDir);
  await updatePackageFiles(targetDir, packageNameFromRepo(repo));
  await updateAstroConfig(targetDir, options.site, repo);
  await writeStarterPaper(targetDir, options);

  console.log(`Created ${targetDir}`);
  console.log("");
  console.log("Next steps:");
  console.log(`  cd ${path.relative(process.cwd(), targetDir) || "."}`);
  console.log("  npm install");
  console.log("  npm run dev");
  console.log("");
  console.log(
    `Use /${repo}/image/... and /${repo}/videos/... for public assets.`,
  );
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
