import { notFound } from "next/navigation";
import { PostForm } from "@/components/post-form";
import { updatePostAction } from "@/lib/actions";
import { getPost } from "@/lib/posts";

export const dynamic = "force-dynamic";

export default async function EditPostPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const id = Number((await params).id);
  const post = Number.isInteger(id) ? await getPost(id) : null;
  if (!post) notFound();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">글 수정</h1>
      <PostForm
        action={updatePostAction.bind(null, post.id)}
        cancelHref={`/posts/${post.id}`}
        submitLabel="수정"
        defaults={post}
      />
    </div>
  );
}
