<h2>Register new user</h2>
<script>
	function checkRepassword(e) {
		let password = e.target.elements.password.value;
		let repassword = e.target.elements["re-password"].value;
		if (password === repassword) {
			return true;
		}
		alert("password and retype password do not match");
  	e.preventDefault();
  	return false;
  }
</script>
<form id="register-form" method="POST" onsubmit="return checkRepassword(event);">
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
	Retype password
	<br />
	<input type="password" name="re-password" required>
	<br />
	<br />
	<button type="submit">submit</button>
</form>
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!empty($_POST['username']) && !empty($_POST['password'])) {
      if (check_name($_POST['username'])) {
        if (insert_user($_POST['username'], $_POST['password'])) {
          echo '<h3 style="color: green;">Register successfully</h3>';
        } else {
          err('Fail to register');
        }
      } else {
        err('Username already been taken');
      }
    } else {
      err('Missing username or password');
    }
	}
?>