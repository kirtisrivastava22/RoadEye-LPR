export async function postImage(file: File) {
  const formData = new FormData()
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE;
  formData.append("file", file)
  const res = await fetch(`${API_BASE}/detect/image`, {
    method: "POST",
    body: formData,
  })
  return res.json()
}
