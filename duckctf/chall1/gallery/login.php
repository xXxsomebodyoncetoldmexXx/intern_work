<script src="https://www.google.com/recaptcha/api.js" async defer></script>
<script>
   function onSubmit(token) {
     document.getElementById("login-form").submit();
   }
 </script>	
<h2>Login to website</h2>
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
	<button class="g-recaptcha" data-sitekey="6LcVQrIeAAAAALphDnp4iXCn6mgmHIRxQlzNCMbK" data-callback='onSubmit'>Submit</button>
</form>
<h3 style="color: red;">
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
		if (check_captcha_invisible()) {
			if (isset($_POST['username']) && isset($_POST['password']) && $_POST['username'] && $_POST['password']) {
				if (get_user($_POST['username'], $_POST['password'])) {
					$_SESSION['username'] = $username;
					$_SESSION['login'] = true;
  					header('Location: index.php');
				} else {
					echo 'Wrong username or password';
				}
			} else {
				echo 'Missing username or password';
			}
		} else {
			echo 'Invalid captcha or captcha not found!';
		}
	}
?>
</h3>