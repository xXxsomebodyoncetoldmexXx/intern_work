<form id="login-form" method="POST">
	Username
	<br />
	<input type="text" name="username" required>
	<br />
	<br />
	Password
	<br />
	<input type="password" name="password" required>
	<br />
	<br />
	<button type="submit">Submit</button>
</form>
<h3 style="color: red;">
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['username']) && isset($_POST['password']) && $_POST['username'] && $_POST['password']) {
      if ($_POST['username'] === $_POST['password'] && $_POST['username'] === 'admin') {
        $_SESSION['username'] = $username;
        $_SESSION['login'] = true;
        header('Location: index.php');
        die();
      } else {
        echo 'Wrong username or password';
      }
    } else {
      echo 'Missing username or password';
    }
	}
?>
</h3>