import { promises as fs } from "fs";
import path from "path";

export type Post = {
  id: number;
  title: string;
  author: string;
  content: string;
  views: number;
  createdAt: string;
  updatedAt: string;
};

const DB_PATH = path.join(process.cwd(), "data", "posts.json");
export const PAGE_SIZE = 10;

async function readAll(): Promise<Post[]> {
  try {
    return JSON.parse(await fs.readFile(DB_PATH, "utf-8"));
  } catch {
    return [];
  }
}

async function writeAll(posts: Post[]) {
  await fs.mkdir(path.dirname(DB_PATH), { recursive: true });
  await fs.writeFile(DB_PATH, JSON.stringify(posts, null, 2), "utf-8");
}

export async function listPosts(page = 1, query = "") {
  const q = query.trim().toLowerCase();
  const all = (await readAll())
    .filter(
      (p) =>
        !q ||
        p.title.toLowerCase().includes(q) ||
        p.content.toLowerCase().includes(q) ||
        p.author.toLowerCase().includes(q),
    )
    .sort((a, b) => b.id - a.id);
  const totalPages = Math.max(1, Math.ceil(all.length / PAGE_SIZE));
  const current = Math.min(Math.max(1, page), totalPages);
  return {
    posts: all.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE),
    total: all.length,
    page: current,
    totalPages,
  };
}

export async function getPost(id: number) {
  return (await readAll()).find((p) => p.id === id) ?? null;
}

export async function increaseViews(id: number) {
  const posts = await readAll();
  const post = posts.find((p) => p.id === id);
  if (!post) return null;
  post.views += 1;
  await writeAll(posts);
  return post;
}

export async function createPost(
  data: Pick<Post, "title" | "author" | "content">,
) {
  const posts = await readAll();
  const now = new Date().toISOString();
  const post: Post = {
    id: posts.reduce((m, p) => Math.max(m, p.id), 0) + 1,
    ...data,
    views: 0,
    createdAt: now,
    updatedAt: now,
  };
  posts.push(post);
  await writeAll(posts);
  return post;
}

export async function updatePost(
  id: number,
  data: Pick<Post, "title" | "author" | "content">,
) {
  const posts = await readAll();
  const post = posts.find((p) => p.id === id);
  if (!post) return null;
  Object.assign(post, data, { updatedAt: new Date().toISOString() });
  await writeAll(posts);
  return post;
}

export async function deletePost(id: number) {
  const posts = await readAll();
  await writeAll(posts.filter((p) => p.id !== id));
}
