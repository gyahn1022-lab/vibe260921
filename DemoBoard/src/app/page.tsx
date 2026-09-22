import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LinkButton } from "@/components/link-button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listPosts } from "@/lib/posts";

export const dynamic = "force-dynamic";

export default async function HomePage({ searchParams }: PageProps<"/">) {
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q : "";
  const pageParam = Number(typeof sp.page === "string" ? sp.page : 1) || 1;
  const { posts, total, page, totalPages } = await listPosts(pageParam, q);

  const href = (p: number) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    params.set("page", String(p));
    return `/?${params}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <form className="flex gap-2" action="/">
          <Input
            name="q"
            defaultValue={q}
            placeholder="제목, 내용, 작성자 검색"
            className="w-64"
          />
          <Button type="submit" variant="secondary">
            검색
          </Button>
        </form>
        <LinkButton href="/posts/new">글쓰기</LinkButton>
      </div>

      <p className="text-sm text-muted-foreground">총 {total}개의 게시글</p>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-16">번호</TableHead>
            <TableHead>제목</TableHead>
            <TableHead className="w-28">작성자</TableHead>
            <TableHead className="w-28">작성일</TableHead>
            <TableHead className="w-16 text-right">조회</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {posts.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={5}
                className="h-24 text-center text-muted-foreground"
              >
                게시글이 없습니다.
              </TableCell>
            </TableRow>
          ) : (
            posts.map((p) => (
              <TableRow key={p.id}>
                <TableCell>{p.id}</TableCell>
                <TableCell>
                  <Link
                    href={`/posts/${p.id}`}
                    className="font-medium hover:underline"
                  >
                    {p.title}
                  </Link>
                </TableCell>
                <TableCell>{p.author}</TableCell>
                <TableCell>{p.createdAt.slice(0, 10)}</TableCell>
                <TableCell className="text-right">{p.views}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          {page > 1 ? (
            <LinkButton variant="outline" size="sm" href={href(page - 1)}>이전</LinkButton>
          ) : (
            <Button variant="outline" size="sm" disabled>
              이전
            </Button>
          )}
          <span className="text-sm">
            {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <LinkButton variant="outline" size="sm" href={href(page + 1)}>다음</LinkButton>
          ) : (
            <Button variant="outline" size="sm" disabled>
              다음
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
