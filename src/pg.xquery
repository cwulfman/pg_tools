xquery version "3.1";


let $entries := //div[@type = 'entry']

let $persNames := //div[@type = 'entry']/bibl/persName

let $persRefs := //div[@type = 'entry']/bibl/ref

let $entries_without_bibls :=
 for $e in $entries
 where $e[not(bibl)]
 return $e

let $anonymous_entries :=
 for $e in $entries
 where  $e[not(bibl/persName)]
 return $e

let $report := <report>
<entries>{count($entries)}</entries>
<persNames>{count($persNames)}</persNames>
<persRefs>{count($persRefs)}</persRefs>
<entriesWithoutBibls>{count($entries_without_bibls)}</entriesWithoutBibls>
<anonymous_entries>{count($anonymous_entries)}</anonymous_entries>
</report>

let $works := //div[@type='entry']/p/bibl
return 
<works>
{ 
  for $work in $works
  let $id := $work/@xml:id
  let $volume := 
    if ($work/ref[@type='volume']/@n)
   then
    $work/ref[@type='volume']/@n
   else
    $work/ref[@type='volume'] 

  let $start :=
  if ($work/ref[@type='column1']/@n)
   then
    $work/ref[@type='column1']/@n
   else
    $work/ref[@type='column1'] 
  let $end :=
  if ($work/ref[@type='column2']/@n)
   then
    $work/ref[@type='column2']/@n
   else
    $work/ref[@type='column2']   
  return <work id="{$id}" volume="{$volume}" start="{$start}" end="{$end}" />
}
</works>