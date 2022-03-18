<script>
   function onSubmit(token) {
     document.getElementById("upload-form").submit();
   }
 </script>	
<?php
	function debug($msg) {
		echo "<h3>$msg</h3>";
	}

	function err($msg) {
		die("<h3 style='color:red;'>$msg</h3>");
	}

	function check_valid_file() {
		// Check ext
		if (pathinfo($_FILES['imgfile']['name'], PATHINFO_EXTENSION) === 'gif') {
			// Check filetype
			$gif = imagecreatefromgif($_FILES['imgfile']['tmp_name']);
			if ($gif) {
				return true;
			}
		} 
		return false;
	}

	if (isset($_SESSION['login']) && $_SESSION['login']) {
		if ($_SERVER['REQUEST_METHOD'] === 'GET') {
			echo "<form id='upload-form' method='POST' enctype='multipart/form-data'>
				<label for='ffile'>Choose a file to upload: </label>
				<input type='file' id='ffile' name='imgfile'>
				<br />
				<button type='submig'>Submit</button>
			</form>
			<h4>Server only accept gif file</h4>";
		} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
			// array(1) { ["imgfile"]=> array(5) { ["name"]=> string(9) "Server.py" ["type"]=> string(13) "text/x-python" ["tmp_name"]=> string(14) "/tmp/phpTise6s" ["error"]=> int(0) ["size"]=> int(9092) } }
			if (check_valid_file()) {
				$rootdir = "uploaded/";
				$savepath = $rootdir . bin2hex(random_bytes(12)) . "/";
				$savefile = $savepath . $_FILES['imgfile']['name'];
				mkdir($savepath);

				move_uploaded_file($_FILES['imgfile']['tmp_name'], $savefile);
				echo "<a href='gallery/$savefile'>success</a>";
			}
		}
	} else {
		echo '<h3>Please login</h3>';
	}
?>
