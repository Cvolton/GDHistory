<?php
require('vendor/callumacrae/plist/plist.php');
require('incl/connection.php');

define("MAX_K", 94);

function buildFullArray($level){
    $newArray = [];
    for($i = 1; $i <= MAX_K; $i++){
        if($i == 4)
            continue;
        $newArray["k$i"] = isset($level["k$i"]) ? $level["k$i"] : null;
    }
    return $newArray;
}

function buildLevelSQLQuery(){
    $columns = $constants = "";
    for($i = 1; $i <= MAX_K; $i++){
        if($i == 4)
            continue;
        $columns .= "k$i, ";
        $constants .= ":k$i, ";
    }
    return "INSERT INTO level ($columns save_data_id) VALUES ($constants :save_data_id)";
}

function decryptCCFile($content){
    $size = strlen($content);
    $result = "";

    for($i = 0; $i < $size; $i++)
        $result[$i] = chr(ord($content[$i]) ^ 11);

    return $result;
}

function decodeUrlSafeBase64($content){
    $content = str_replace("-","+",$content);
    $content = str_replace("_","/",$content);
    return base64_decode($content);
}

function parseCCFile($filename){
    $content = file_get_contents($filename);
    if(substr($content, 0, 7) == "C?xBJJJ")
        $content = decodeCCFile($content);
    if(substr($content, 0, 5) != "<?xml")
        return null;
    file_put_contents('tmp', robtopPlistToPlist(removeInvalidXMLChars($content)));
    return plist::Parse('tmp');
}

function decodeCCFile($content){
    return gzdecode(decodeUrlSafeBase64(decryptCCFile($content)));
}

function removeInvalidXMLChars($content){
    return str_replace("&#24", "@@24", str_replace("&#26", "@@26", $content));
}

function robtopPlistToPlist($content){
    //this is one of the most stupid functions known to mankind
    return
    str_replace("</d>", "</dict>", 
    str_replace("</k>", "</key>", 
    str_replace("<d>", "<dict>", 
    str_replace("<k>","<key>", 
    str_replace("<s>","<string>",
    str_replace("</s>","</string>",
    str_replace("<i>","<integer>",
    str_replace("</i>","</integer>",
    str_replace("<t />","<true />",
    str_replace("<r>","<real>",
    str_replace("</r>","</real>",
    $content)))))))))));
}

function uploadSaveFile($db, $date, $array){
    $save_data_id = $db->prepare('INSERT INTO save_data (account_id, time_saved) VALUES (:account_id, :timestamp)');
    $save_data_id->execute(['account_id' => 1, 'timestamp' => $date]);
    $save_data_id = $db->lastInsertId();

    $GLM_03 = $array['GLM_03'];

    foreach($GLM_03 as &$level){
        $fullArray = buildFullArray($level);
        $fullArray['save_data_id'] = $save_data_id;
        $insertQuery = $db->prepare(buildLevelSQLQuery());
        $insertQuery->execute($fullArray);
        echo "inserted level {$fullArray['k1']}\r\n";
        if(isset($level['k4'])){
            $id = $db->lastInsertId();
            file_put_contents("data/k4/$id", $level['k4']);
        }
    
    }

    copy('tmp', "data/saves/$save_data_id");
}

//START OF TEMPORARY CODE FOR CVOLTON DB IMPORT
$dir = new DirectoryIterator("L:\\My Drive\\laptop_oldwindows\\cbackup\\GeometryDash\\save_backups");
foreach ($dir as $fileinfo) {
    if ($fileinfo->isDot())
        continue;
    $filename = $fileinfo->getFilename();
    $filename = "L:\\My Drive\\laptop_oldwindows\\cbackup\\GeometryDash\\save_backups\\{$filename}\\CCGameManager.dat";
    $date = date("Y-m-d", strtotime(explode(" ",$fileinfo->getFilename())[0]));
    echo "$filename : $date";
    //echo "{$date['year']}-{$date['month']}-{$date['day']}";

    //END OF TEMPORARY CODE FOR CVOLTON DB IMPORT
    

    $array = parseCCFile($filename);
    uploadSaveFile($db, $date, $array);
    
    

    //START OF TEMPORARY CODE FOR CVOLTON DB IMPORT
}
/*
$filename = "L:\\My Drive\\laptop_oldwindows\\cbackup\\GeometryDash\\CCGameManager.dat";
$date = "2019-12-02";
$array = parseCCFile($filename);
uploadSaveFile($db, $date, $array);
*/