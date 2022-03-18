<form id="add-form" method="POST">
	Title
	<br />
	<input type="text" name="title" required>
	<br />
	<br />
	Content
	<br />
	<textarea name="content" cols="30" rows="10" required></textarea>
	<br />
	<br />
	<button type="submit">Submit</button>
</form>
<h3 style="color: red;">
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!empty($_POST['title']) && !empty($_POST['content'])) {
      insert_news($_POST['title'], 'admin', $_POST['content']);
      header('Location: index.php');
      die();
    } else {
      echo 'Article title and content must not be empty';
    }
	}
?>
</h3>