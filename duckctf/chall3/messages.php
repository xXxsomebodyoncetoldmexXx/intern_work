<h2>Create new message</h2>
<form id="send-msg-form" method="POST">
	Receive User
	<br />
	<input type="text" name="recv-user" required>
	<br />
	<br />
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
	<button type="submit">submit</button>
</form>
<?php
	if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!empty($_POST['recv-user']) && !empty($_POST['title']) && !empty($_POST['content'])) {
      $row = get_user_by_name($_POST['recv-user']);
      if ($row->{"num_rows"} == 1) {
        $row = $row->fetch_assoc();
        insert_msg($_POST['title'], $_POST['content'], $_SESSION['uid'], $row['id']);
      }
      echo "<h3 style='color:green;'>Message send</h3>";
    } else {
      err('Missing receiver, title or content of the message.');
    }
	}
?>
<br /><hr />
<h2>Received messages</h2>
<?php 
if (empty($_GET['mid'])) {
  ?>
  <table>
    <tr>
      <th>Id</th>
      <th>Title</th>
      <th>Author</th>
      <th>Receiver</th>
      <th>Date</th>
    </tr>
    <?php
    if ($_SESSION['isadmin']) {
      $msgs = get_msg();
    } else {
      $msgs = get_own_msg($_SESSION['uid']);
    }
    while ($row = $msgs->fetch_assoc()) {
      $sender = get_user_by_id($row['sender'])->fetch_assoc();
      $receiver = get_user_by_id($row['receiver'])->fetch_assoc();
      echo "<tr onClick=\"window.location.href = '/?mid=" . $row['id'] . "'\">";
      echo "<td>" . $row['id'] . "</td>";
      echo "<td>" . htmlentities($row['title']) . "</td>";
      echo "<td>" . htmlentities($sender['username']) . "</td>";
      echo "<td>" . htmlentities($receiver['username']) . "</td>";
      echo "<td>" . $row['reg_date'] . "</td>";
      echo "</tr>";
    }
    ?>
  </table>
  <?php
} else {
  $msg = get_msg_by_id($_GET['mid']);
  if ($msg->{"num_rows"}) {
    $row = $msg->fetch_assoc();
    if ($_SESSION['isadmin'] || $row['receiver'] === $_SESSION['uid']) {
      $sender = get_user_by_id($row['sender'])->fetch_assoc();
      echo "<h2>Title: " . htmlentities($row['title']) . "</h2>";
      echo "<h5>Author: " . htmlentities($sender['username']) . " - Date: " . $row['reg_date'] . "</h5>";
      echo "<br /><br />";
      echo "<pre>" . $row['content'] . "</pre>";
      echo "<br /><hr />";
      if ($_SESSION['isadmin']) {
        echo '<input type="button" onclick="location.href=\'?mid=' . $row['id'] . '&action=delete\';" value="Delete" />';
      }
    } else {
      err("User don't have permission to see msg");
    }
  } else {
    err("No message found!");
  }
}