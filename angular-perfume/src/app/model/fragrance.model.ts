// @dynamic
export class Fragrance {
    name: string;
    notes: string[] = [];
    tags: string[] = [];
    body: string;
    score: number;
    rank: number = 0;
    orderScore: number = 0;
    ranked: boolean = false;
    longVec: number[] = [];
    shortVec: number[] = [];

    constructor(obj?: any){
        if (obj){
            this.name = obj.name;
            this.notes = obj.notes.map(elem => this.trimText(elem));
            this.tags = obj.tags.map(elem => this.trimText(elem));
            this.body = obj.body;
            this.longVec = obj.long_vec;
            this.shortVec = obj.simple_vec;
        }
    }

    getWordSet(): Set<string>{
      let allKeywords = this.tags.concat(this.notes);
      let wordSet: Set<string> = new Set(allKeywords);
      return wordSet;
    }

    getRankedMap(): Map<string, number>{
        let ranks = new Map();
        for (let note of this.notes){
            ranks.set(note, 1.5);
        }
        for (let tag of this.tags){
            let currentValue = ranks.get(tag) ? ranks.get(tag) + .5 : 1.5;
            ranks.set(tag, currentValue);
        }
        return ranks;
    }

    private trimText(text: string): string{
        return text.toLowerCase().replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"").replace(/\s{2,}/g," ");
    }
}
    