interface Aircraft
{
    id: string;
    regNo: string;
    compNo?: string;
    type: string;
    seats: number;
}

class AircraftRecognizer
{
    constructor(aircrafts: Aircraft[])
    {
        this.aircrafts = aircrafts;
    }

    recognize(s: string): boolean
    {
        console.log(`${s} ${this.regNo}`);
        if( s == this.regNo )
            return true;

        return false;
    }
}

r = new AircraftRecognizer([
    {id: "1", regNo: "D-8883", compNo: "RJ", type: "Std. Libelle", seats: 1},
    {id: "2", regNo: "D-2074", type: "ASK 13", seats: 2},
    {id: "3", regNo: "D-8984", type: "ASK 13", seats: 2},
    {id: "4", regNo: "D-5014", compNo: "YX", type: "Duo Discus", seats: 2}
]);

for( let i of aircrafts )
    console.log(i.recognize("D-8883"));



interface Person
{
    id: string;
    lastName: string;
    firstName: string;
}

let persons = [
  {
    "id": "5b3166469c0412b138df0ee1",
    "lastName": "Knight",
    "firstName": "Mills"
  },
  {
    "id": "5b316646133625b55a8a6a7f",
    "lastName": "Welch",
    "firstName": "Beryl"
  },
  {
    "id": "5b316646e171d14c0c62fa75",
    "lastName": "Hensley",
    "firstName": "Pollard"
  },
  {
    "id": "5b316646b345f39a3cc48b67",
    "lastName": "Richard",
    "firstName": "Mcmillan"
  },
  {
    "id": "5b316646292009736405f229",
    "lastName": "Prince",
    "firstName": "Castillo"
  },
  {
    "id": "5b316646d7ac9d20aa923b79",
    "lastName": "Rivas",
    "firstName": "Jackson"
  },
  {
    "id": "5b31664665b15c278e582d3f",
    "lastName": "Decker",
    "firstName": "Adriana"
  }
];

interface Location
{
    id: string;
    icao: string;
    short: string;
    name: string;
}

let locations = [
    {id: "1", icao: "EDLW", short: "dtm", name: "Dortmund"},
    {id: "2", icao: null, short: "rhmk", name: "Iserlohn-Rheinermark"},
    {id: "3", icao: null, short: null, name: "Hengsen-Opherdicke"},
    {id: "4", icao: null, short: null, name: "Iserlohn-Sümmern"},
    {id: "5", icao: null, short:null, name: "Altena-Hegenscheidt"},
];

