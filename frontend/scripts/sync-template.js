import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distPath = path.resolve(__dirname, '../dist/index.html');
const templatePath = path.resolve(__dirname, '../../VinShop/templates/index.jinja2');

const distHtml = fs.readFileSync(distPath, 'utf-8');

// 从 dist/index.html 中提取 CSS 和 JS 路径
const cssMatch = distHtml.match(/href="(\/assets\/index-[^"]+\.css)"/);
const jsMatch = distHtml.match(/src="(\/assets\/index-[^"]+\.js)"/);

if (!cssMatch) {
  console.error('未找到 CSS 路径');
  process.exit(1);
}
if (!jsMatch) {
  console.error('未找到 JS 路径');
  process.exit(1);
}

const cssPath = cssMatch[1];
const jsPath = jsMatch[1];
console.log(`CSS: ${cssPath}`);
console.log(`JS:  ${jsPath}`);

// 更新模板中的 CSS 和 JS 引用
let template = fs.readFileSync(templatePath, 'utf-8');
template = template.replace(
  /href="\/assets\/index-[^"]+\.css"/,
  `href="${cssPath}"`
);
template = template.replace(
  /src="\/assets\/index-[^"]+\.js"/,
  `src="${jsPath}"`
);

fs.writeFileSync(templatePath, template, 'utf-8');
console.log(`模板已更新: ${templatePath}`);
