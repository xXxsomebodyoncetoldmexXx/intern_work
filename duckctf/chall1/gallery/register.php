<script src="https://www.google.com/recaptcha/api.js?onload=onloadCallback&render=explicit" async defer></script>
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
	<div id="captcha-box" style="position: relative;"></div>
    <br />
    <br />
	<button>submit</button>
</form>
<h3 style="color: red;">
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
		if (check_captcha_checkbox()) {
			if (isset($_POST['username']) && isset($_POST['password']) && $_POST['username'] && $_POST['password']) {
				if (check_name($_POST['username'])) {
					if (insert_user($_POST['username'], $_POST['password'])) {
						echo '<h3>Register successfully</h3>';
					} else {
						echo 'Fail to register';
					}
				} else {
					echo 'Username already been taken';
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
<script type="text/javascript">
	var onloadCallback = function() {
        grecaptcha.render('captcha-box', {
          'sitekey' : '6LeyIMEeAAAAAOia0VrSnvZyXWBKBye1tbVprYan'
        });
      };
</script>