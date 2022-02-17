function prepfile(id, target) {
  const file = document.getElementById(id).files[0];
  const reader = new FileReader();
  if (file) {
    reader.onload = () => {
      document.getElementById(target).value = reader.result;
    };
    reader.onerror = () => console.log;
    reader.readAsDataURL(file);
  }
}
