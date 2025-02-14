let rec intersperse (l: (Z.t) list) (n: Z.t) : (Z.t) list =
  match l with
  | [] -> [] 
  | x :: ([]) -> x :: [] 
  | x :: xs ->
    (let o = let result = intersperse xs n in n :: result in x :: o)

let rec nth_1 (n: Z.t) (l: (Z.t) list) : Z.t =
  match l with
  | x :: r -> if Z.equal n Z.zero then x else nth_1 (Z.sub n Z.one) r
  | _ -> assert false (* absurd *)

let list_eq (l1: (Z.t) list) (l2: (Z.t) list) : bool =
  let n = Z.of_int (List.length l1) in
  let res = ref true in
  (let o = Z.sub n Z.one in let o1 = Z.zero in
   let rec for_loop_to i =
     if Z.leq i o
     then begin
       if not (Z.equal (nth_1 i l1) (nth_1 i l2)) then res := false;
       for_loop_to (Z.succ i)
     end
   in for_loop_to o1);
  !res

let test1 (_: unit) : bool =
  let o = intersperse ([] ) (Z.of_string "5") in list_eq o ([] )

let test1_output (_: unit) :
  ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  let o = intersperse ([] ) (Z.of_string "5") in
  ([] , Z.of_string "5", o, [] )

let test2 (_: unit) : bool =
  let o = intersperse (Z.one :: [] ) (Z.of_string "5") in
  list_eq o (Z.one :: [] )

let test2_output (_: unit) :
  ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  let o = intersperse (Z.one :: [] ) (Z.of_string "5") in
  (Z.one :: [] , Z.of_string "5", o, Z.one :: [] )

let test3 (_: unit) : bool =
  let o = intersperse (Z.one :: Z.of_string "2" :: [] ) (Z.of_string "5") in
  list_eq o (Z.one :: Z.of_string "5" :: Z.of_string "2" :: [] )

let test3_output (_: unit) :
  ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  let o = intersperse (Z.one :: Z.of_string "2" :: [] ) (Z.of_string "5") in
  (Z.one :: Z.of_string "2" :: [] , Z.of_string "5", o,
  Z.one :: Z.of_string "5" :: Z.of_string "2" :: [] )

let test4 (_: unit) : bool =
  let o =
    intersperse (Z.one :: Z.of_string "2" :: Z.of_string "3" :: [] )
    (Z.of_string "5") in
  list_eq o
  (Z.one :: Z.of_string "5" :: Z.of_string "2" :: Z.of_string "5" :: 
  Z.of_string "3" :: [] )

let test4_output (_: unit) :
  ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  let o =
    intersperse (Z.one :: Z.of_string "2" :: Z.of_string "3" :: [] )
    (Z.of_string "5") in
  (Z.one :: Z.of_string "2" :: Z.of_string "3" :: [] , Z.of_string "5", o,
  Z.one :: Z.of_string "5" :: Z.of_string "2" :: Z.of_string "5" :: Z.of_string "3" :: 
  [] )

let test5 (_: unit) : bool =
  let o = intersperse (Z.one :: Z.one :: Z.one :: [] ) (Z.of_string "9") in
  list_eq o
  (Z.one :: Z.of_string "9" :: Z.one :: Z.of_string "9" :: Z.one :: [] )

let test5_output (_: unit) :
  ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  let o = intersperse (Z.one :: Z.one :: Z.one :: [] ) (Z.of_string "9") in
  (Z.one :: Z.one :: Z.one :: [] , Z.of_string "9", o,
  Z.one :: Z.of_string "9" :: Z.one :: Z.of_string "9" :: Z.one :: [] )

let testall (_: unit) : bool =
  test1 () && test2 () && test3 () && test4 () && test5 ()

let testfail (_: unit) : (Z.t) list =
  let res = ref ([] ) in
  if not (test1 ()) then res := Z.one :: !res;
  if not (test2 ()) then res := Z.of_string "2" :: !res;
  if not (test3 ()) then res := Z.of_string "3" :: !res;
  if not (test4 ()) then res := Z.of_string "4" :: !res;
  if not (test5 ()) then res := Z.of_string "5" :: !res;
  !res

let runtest (x: Z.t) : ((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list) =
  if Z.equal x Z.one
  then test1_output ()
  else
    begin
      if Z.equal x (Z.of_string "2")
      then test2_output ()
      else
        begin
          if Z.equal x (Z.of_string "3")
          then test3_output ()
          else
            begin
              if Z.equal x (Z.of_string "4")
              then test4_output ()
              else
                begin
                  if Z.equal x (Z.of_string "5")
                  then test5_output ()
                  else ([] , Z.of_string "-1", [] , [] ) end end end end

let rec failoutput (l: (Z.t) list) :
  (((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list)) list =
  match l with
  | [] -> [] 
  | x :: xs ->
    (let result = failoutput xs in let result1 = runtest x in
     result1 :: result)

let test (_: unit) :
  (((Z.t) list) * (Z.t) * ((Z.t) list) * ((Z.t) list)) list =
  let l = testfail () in failoutput l


let () =
  Printf.printf "Running test cases...\n";

  if testall () then
    Printf.printf "All tests passed!\n"
  else begin
    Printf.printf "Some tests failed.\n";
    let failed_tests = testfail () in
    let failed_outputs = failoutput failed_tests in
    List.iter (fun (input_list, separator, result, expected) ->
      Printf.printf "Test failed with input: ";
      List.iter (fun x -> Printf.printf "%s " (Z.to_string x)) input_list;
      Printf.printf "\nSeparator: %s\n" (Z.to_string separator);
      Printf.printf "Expected: ";
      List.iter (fun x -> Printf.printf "%s " (Z.to_string x)) expected;
      Printf.printf "\nGot: ";
      List.iter (fun x -> Printf.printf "%s " (Z.to_string x)) result;
      Printf.printf "\n\n"
    ) failed_outputs
  end
