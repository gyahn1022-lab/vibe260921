import { supabase } from "./supabase";

export type Post = {
  id: number;
  title: string;
  author: string;
  content: string;
  views: number;
  createdAt: string;
  updatedAt: string;
};

type PostDB = {
  id: number;
  title: string;
  author: string;
  content: string;
  views: number;
  created_at: string;
  updated_at: string;
};

function mapPostFromDB(dbPost: PostDB): Post {
  return {
    id: dbPost.id,
    title: dbPost.title,
    author: dbPost.author,
    content: dbPost.content,
    views: dbPost.views,
    createdAt: dbPost.created_at,
    updatedAt: dbPost.updated_at,
  };
}

export const PAGE_SIZE = 10;

export async function listPosts(page = 1, query = "") {
  try {
    const q = query.trim().toLowerCase();

    let baseQuery = supabase
      .from("posts")
      .select("*", { count: "exact" });

    if (q) {
      baseQuery = baseQuery.or(
        `title.ilike.%${q}%,content.ilike.%${q}%,author.ilike.%${q}%`
      );
    }

    const { data, count, error } = await baseQuery
      .order("id", { ascending: false })
      .range((page - 1) * PAGE_SIZE, page * PAGE_SIZE - 1);

    if (error) throw error;

    const total = count || 0;
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const current = Math.min(Math.max(1, page), totalPages);

    const posts = (data as PostDB[])?.map(mapPostFromDB) || [];

    return {
      posts,
      total,
      page: current,
      totalPages,
    };
  } catch (error) {
    console.error("Error listing posts:", error);
    return { posts: [], total: 0, page: 1, totalPages: 1 };
  }
}

export async function getPost(id: number) {
  try {
    const { data, error } = await supabase
      .from("posts")
      .select("*")
      .eq("id", id)
      .single();

    if (error && error.code !== "PGRST116") throw error;
    return data ? mapPostFromDB(data as PostDB) : null;
  } catch (error) {
    console.error("Error getting post:", error);
    return null;
  }
}

export async function increaseViews(id: number) {
  try {
    const post = await getPost(id);
    if (!post) return null;

    const { data, error } = await supabase
      .from("posts")
      .update({ views: post.views + 1 })
      .eq("id", id)
      .select()
      .single();

    if (error) throw error;
    return data ? mapPostFromDB(data as PostDB) : null;
  } catch (error) {
    console.error("Error increasing views:", error);
    return null;
  }
}

export async function createPost(
  data: Pick<Post, "title" | "author" | "content">,
) {
  try {
    const now = new Date().toISOString();
    const { data: newPost, error } = await supabase
      .from("posts")
      .insert([
        {
          title: data.title,
          author: data.author,
          content: data.content,
          views: 0,
          created_at: now,
          updated_at: now,
        },
      ])
      .select()
      .single();

    if (error) throw error;
    return newPost ? mapPostFromDB(newPost as PostDB) : null;
  } catch (error) {
    console.error("Error creating post:", error);
    throw error;
  }
}

export async function updatePost(
  id: number,
  data: Pick<Post, "title" | "author" | "content">,
) {
  try {
    const now = new Date().toISOString();
    const { data: updatedPost, error } = await supabase
      .from("posts")
      .update({
        title: data.title,
        author: data.author,
        content: data.content,
        updated_at: now,
      })
      .eq("id", id)
      .select()
      .single();

    if (error) throw error;
    return updatedPost ? mapPostFromDB(updatedPost as PostDB) : null;
  } catch (error) {
    console.error("Error updating post:", error);
    throw error;
  }
}

export async function deletePost(id: number) {
  try {
    const { error } = await supabase.from("posts").delete().eq("id", id);
    if (error) throw error;
  } catch (error) {
    console.error("Error deleting post:", error);
    throw error;
  }
}
