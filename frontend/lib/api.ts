export async function postImage(file: File) {
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch("http://localhost:8000/detect/image", {
    method: "POST",
    body: formData,
  })
  return res.json()
}
