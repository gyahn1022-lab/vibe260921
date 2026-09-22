"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";
import { createPost, deletePost, updatePost } from "@/lib/posts";

export type FormState = { error?: string } | undefined;

function parse(formData: FormData) {
  const title = String(formData.get("title") ?? "").trim();
  const author = String(formData.get("author") ?? "").trim();
  const content = String(formData.get("content") ?? "").trim();
  if (!title || !author || !content) {
    return { error: "제목, 작성자, 내용을 모두 입력해주세요." } as const;
  }
  if (title.length > 100 || author.length > 30) {
    return { error: "제목은 100자, 작성자는 30자 이내로 입력해주세요." } as const;
  }
  return { data: { title, author, content } } as const;
}

export async function createPostAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const parsed = parse(formData);
  if ("error" in parsed) return { error: parsed.error };
  const post = await createPost(parsed.data);
  revalidatePath("/");
  redirect(`/posts/${post.id}`);
}

export async function updatePostAction(
  id: number,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const parsed = parse(formData);
  if ("error" in parsed) return { error: parsed.error };
  await updatePost(id, parsed.data);
  revalidatePath("/");
  revalidatePath(`/posts/${id}`);
  redirect(`/posts/${id}`);
}

export async function deletePostAction(id: number) {
  await deletePost(id);
  revalidatePath("/");
  redirect("/");
}
