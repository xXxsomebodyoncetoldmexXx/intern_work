function uploadFile() {
  const file = document.getElementById('uploadFile').files[0];
  document.getElementById('uploadFile').value = '';
  const path = document.location.pathname;
  if (file !== undefined) {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      axios
        .post(
          path,
          { ip: reader.result },
          {
            headers: {
              'Content-Type': 'application/json',
            },
          }
        )
        .then((res) => {
          setTimeout(() => {
            location.reload();
          }, 1000);
        })
        .catch(console.log);
    };
  }
}
