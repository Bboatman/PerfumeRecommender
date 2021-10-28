import { Fragrance } from "./fragrance.model";

// @dynamic
export class User {
    preferences: Map<string, number>
    liked: Fragrance[] = [];
    min: number = 0;
    max: number = 0;

    constructor(){
        this.preferences = new Map<string, number>();
    }

    public getFragranceMatchScore(fragrance: Fragrance): number{
        let results: number[] = [];
        let userArr: number[] = [];
        let rankedMap = fragrance.getRankedMap();
        for (let key of rankedMap.keys()){
            if (this.preferences.get(key)){
                userArr.push(this.normalizeScore(this.preferences.get(key)));
            } else {
                userArr.push(0);
            }
            results.push((rankedMap.get(key) / 2));
        }

        fragrance.score = this.cosinesim(userArr, results);
        return this.cosinesim(userArr, results);
    }

    public rankFragrance(rank: number, fragrance: Fragrance): void{
        for (let word of fragrance.getWordSet()){
            if (this.preferences.has(word)){ 
                let score = this.preferences.get(word) + rank
                this.preferences.set(word, score);
                if (this.min > score){
                    this.min = score;
                } else if (this.max < score){
                    this.max = score
                }
            } else{
                this.preferences.set(word, rank);
                if (this.min > rank){
                    this.min = rank;
                } else if (this.max < rank){
                    this.max = rank
                }
            }
        }
    }

    public addFragranceToFavorites(fragrance: Fragrance): void{
        if (this.liked.length <= 0){
            this.liked = [fragrance]
        } else {
            this.liked.push(fragrance);
        }
    }

    public normalizeScore(score: number): number{
        return ((score-this.min)/(this.max - this.min))
    }

    public cosinesim(vec1: number[], vec2: number[]): number{
        let len = vec1.length
        let numerator = 0;
        let left = 0;
        let right = 0;
        for (let x = 0; x < len; x++){
            numerator += (vec1[x] * vec2[x]);
            left += Math.pow(vec1[x], 2);
            right += Math.pow(vec2[x], 2);
        }
        
        if (left == 0 || right == 0){
            return 0;
        }
        return numerator / (Math.sqrt(left) * Math.sqrt(right));
    }
}

    