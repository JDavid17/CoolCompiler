class Main inherits IO{

  main(): Object {
        case 1 of
            n : Int => out_int(n);
            n : Bool => out_string("Burro");
        esac
   };
};
