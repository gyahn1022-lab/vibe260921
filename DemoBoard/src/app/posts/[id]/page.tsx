import { notFound } from "next/navigation";
import { LinkButton } from "@/components/link-button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DeleteButton } from "@/components/delete-button";
import { increaseViews } from "@/lib/posts";

export const dynamic = "force-dynamic";

export default async function PostPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const id = Number((await params).id);
  const post = Number.isInteger(id) ? await increaseViews(id) : null;
  if (!post) notFound();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">{post.title}</CardTitle>
          <p className="text-sm text-muted-foreground">
            {post.author} · {post.createdAt.slice(0, 16).replace("T", " ")} ·
            조회 {post.views}
          </p>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap leading-relaxed">{post.content}</p>
        </CardContent>
      </Card>
      <div className="flex justify-between">
        <LinkButton variant="outline" href="/">목록</LinkButton>
        <div className="flex gap-2">
          <LinkButton variant="secondary" href={`/posts/${post.id}/edit`}>
            수정
          </LinkButton>
          <DeleteButton id={post.id} />
        </div>
      </div>
    </div>
  );
}
