class Aircraft
{
    var id;
    regNo: string;
    compNo?: string;
    type: string;
    seats: number;

    recognize(s: string): boolean
    {
        console.log(`${s} ${this.regNo}`);
        if( s == this.regNo )
            return true;

        return false;
    }
}

let aircrafts: Aircraft[] = [
    {id: "1", regNo: "D-8883", compNo: "RJ", type: "Std. Libelle", seats: 1},
    {id: "2", regNo: "D-2074", type: "ASK 13", seats: 2},
    {id: "3", regNo: "D-8984", type: "ASK 13", seats: 2},
    {id: "4", regNo: "D-5014", compNo: "YX", type: "Duo Discus", seats: 2}
];

for( let i of aircrafts )
    console.log(i.recognize("D-8883"));
