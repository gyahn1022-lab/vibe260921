import { LinkButton } from "@/components/link-button";

export default function NotFound() {
  return (
    <div className="space-y-4 py-16 text-center">
      <h1 className="text-2xl font-bold">게시글을 찾을 수 없습니다</h1>
      <LinkButton href="/">목록으로</LinkButton>
    </div>
  );
}
