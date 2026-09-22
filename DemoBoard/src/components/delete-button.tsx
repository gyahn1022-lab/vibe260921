"use client";

import { Button } from "@/components/ui/button";
import { deletePostAction } from "@/lib/actions";

export function DeleteButton({ id }: { id: number }) {
  return (
    <form
      action={deletePostAction.bind(null, id)}
      onSubmit={(e) => {
        if (!confirm("이 게시글을 삭제할까요?")) e.preventDefault();
      }}
    >
      <Button type="submit" variant="destructive">
        삭제
      </Button>
    </form>
  );
}
