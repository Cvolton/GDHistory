<style>
table, th, td {
  border: 1px solid black;
  font-family: monospace;
  text-align: right;
  font-size: 1.2em;
}
</style>

<?php
require('incl/connection.php');

$id = $_GET['id'];
$info = $db->prepare('SELECT level.*, save_data.id, save_data.time_saved FROM `level` INNER JOIN save_data ON level.save_data_id = save_data.id WHERE level.k1 = :id ORDER BY save_data.time_saved ASC');
$info->execute([':id' => $id]);
$info = $info->fetchAll();

echo "<table><tr><th>Time saved</th><th>Level ID</th><th>Level name</th><th>Downloads</th><th>Likes</th><th>Dislikes</th><th>Level Version</th><th>User ID</th><th>Username</th><th>Account ID</th></tr>";

$lastDownloads = -1;
foreach($info as $row){
    if($row['k11'] == $lastDownloads)
        continue;
    $lastDownloads = $row['k11'];
    
    echo "<tr><td>{$row['time_saved']}</td><td>{$row['k1']}</td><td>{$row['k2']}</td><td>{$row['k11']}</td><td>{$row['k22']}</td><td>{$row['k24']}</td><td>{$row['k16']}</td><td>{$row['k6']}</td><td>{$row['k5']}</td><td>{$row['k60']}</td></tr>";
}

echo "</table>";
