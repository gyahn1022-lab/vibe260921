"use client";

import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import { LinkButton } from "@/components/link-button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { FormState } from "@/lib/actions";

type Props = {
  action: (prev: FormState, formData: FormData) => Promise<FormState>;
  cancelHref: string;
  submitLabel: string;
  defaults?: { title: string; author: string; content: string };
};

export function PostForm({ action, cancelHref, submitLabel, defaults }: Props) {
  const [state, formAction, pending] = useActionState(action, undefined);

  return (
    <form action={formAction} className="space-y-5">
      <div className="space-y-2">
        <Label htmlFor="title">제목</Label>
        <Input
          id="title"
          name="title"
          maxLength={100}
          defaultValue={defaults?.title}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="author">작성자</Label>
        <Input
          id="author"
          name="author"
          maxLength={30}
          defaultValue={defaults?.author}
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="content">내용</Label>
        <Textarea
          id="content"
          name="content"
          rows={12}
          defaultValue={defaults?.content}
          required
        />
      </div>
      {state?.error && (
        <p className="text-sm text-destructive" role="alert">
          {state.error}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <LinkButton variant="outline" href={cancelHref}>취소</LinkButton>
        <Button type="submit" disabled={pending}>
          {pending ? "저장 중..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
