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
    if (!empty($_POST['username']) && !empty($_POST['password'])) {
      $row = get_user($_POST['username'], $_POST['password']);
      if ($row->{"num_rows"} === 1) {
        $row = $row->fetch_assoc();
        $_SESSION['username'] = $username;
        $_SESSION['uid'] = $row['id'];
        $_SESSION['login'] = true;
        $_SESSION['isadmin'] = $row['isadmin'];
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