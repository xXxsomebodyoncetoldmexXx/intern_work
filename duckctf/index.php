<!DOCTYPE html>
<html>
<head>
	<title>Duck CTF</title>
    <script src="https://www.google.com/recaptcha/api.js" async defer></script>
</head>
<body>
	<link rel="stylesheet" property="stylesheet" type="text/css" href="s.css" media="all">
	<iframe src="iframe.html"></iframe>

	<h1>Hello world</h1>
	<form id="register-form" method="POST">
		<button class="g-recaptcha" data-sitekey="6LcVQrIeAAAAALphDnp4iXCn6mgmHIRxQlzNCMbK" data-callback='submitForm'>submit</button>
	</form>
	<?php
		$url = "https://www.google.com/recaptcha/api/siteverify";
		if (isset($_POST["g-recaptcha-response"])) {
			$fields = [
				"secret" => "6LcVQrIeAAAAACdvERQKFaNlCaaji22p8coOiaF_",
				"response" => $_POST["g-recaptcha-response"]
			];
			$fields_str = http_build_query($fields);
			echo "<h4>fields:". $fields_str ."</h4><br /><br />";

			// Curl
			$ch = curl_init();
			curl_setopt($ch, CURLOPT_URL, $url);
			curl_setopt($ch, CURLOPT_POST, true);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $fields_str);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

			$res = curl_exec($ch);
			curl_close($ch);
			echo "her";	
			var_dump($res);
		}
	?>
	<script type="text/javascript">
		function submitForm(token) {
			document.getElementById("register-form").submit()
		}
	</script>
</body>
</html>