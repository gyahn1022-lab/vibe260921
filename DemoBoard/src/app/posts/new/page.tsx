import { PostForm } from "@/components/post-form";
import { createPostAction } from "@/lib/actions";

export default function NewPostPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">새 글 작성</h1>
      <PostForm action={createPostAction} cancelHref="/" submitLabel="등록" />
    </div>
  );
}
