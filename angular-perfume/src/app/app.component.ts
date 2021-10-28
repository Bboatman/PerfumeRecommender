import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl } from '@angular/forms'
import { Observable } from 'rxjs';
import {map, startWith} from 'rxjs/operators';
import  *  as  data  from  "./model/data.json";
import { Fragrance } from './model/fragrance.model';
import { User } from './model/user.model';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'BPAL Fragrance Recommender';
  noteMap: Map<string, Fragrance[]> = new Map()
  fragrances: Fragrance[];
  user: User;
  displayArr: Fragrance[] = [];
  currentFragrance: Fragrance;
  filteredOptions: Observable<string[]>;
  myControl = new FormControl();
  isValidSearch: boolean = false;
  bestMatch: boolean = false;

  constructor(){
    let fragrances = []
    this.user = new User();

    for (let dataPoint of data.default){
      let fragrance: Fragrance = new Fragrance(dataPoint);
      fragrances.push(fragrance);
      let wordSet: Set<string> = fragrance.getWordSet();

      for (let keyword of wordSet){
        if (this.noteMap.has(keyword)){
          let newArr = this.noteMap.get(keyword); 
          newArr.push(fragrance);
          this.noteMap.set(keyword, newArr);
        } else {
          this.noteMap.set(keyword, [fragrance]);
        }
      }
    }

    this.fragrances = fragrances;
    const shuffled = [...this.fragrances].sort(() => 0.5 - Math.random());
    this.fragrances.sort(function(a, b){
      if(a.name < b.name) { return -1; }
      if(a.name > b.name) { return 1; }
      return 0;
    })
    this.displayArr = shuffled.slice(0, 6);
    this.currentFragrance = this.displayArr.shift();
  } 

  ngOnInit() {
    this.filteredOptions = this.myControl.valueChanges
      .pipe(
        startWith(''),
        map(value => this._filter(value))
      );

    this.myControl.valueChanges.subscribe(elem => {
      console.log(elem);
      const filterValue = elem.toLowerCase();
      let names = this.fragrances.map(elem => elem.name.toLowerCase());
      this.isValidSearch = names.includes(filterValue);
    })
    this.myControl.value
  }

  sortByClosestMatches(){
    for (let a of this.fragrances){
      let bestMatch: number = 0;
      for (let fragrance of this.fragrances){
        if (fragrance.name != a.name){
          let score: number = this.user.cosinesim(a.shortVec, fragrance.shortVec);
          bestMatch = score > bestMatch ? score : bestMatch;
        }
      }
    }

    this.fragrances.sort(function(a, b){
      if(a.name < b.name) { return -1; }
      if(a.name > b.name) { return 1; }
      return 0;
    })
  }

  private _filter(value: string): string[] {
    const filterValue = value.toLowerCase();
    return this.fragrances.map(elem => elem.name).filter(option => option.toLowerCase().includes(filterValue));
  }

  clearSearch(){
    this.myControl.reset();
  }

  submitSearch(){
    const filterValue = this.myControl.value.toLowerCase();
    let ind = this.fragrances.map(elem => elem.name.toLowerCase()).indexOf(filterValue);
    this.displayArr = [this.currentFragrance].concat(this.displayArr);
    this.currentFragrance = this.fragrances[ind];
  }

  toggleMatch(calculateBestMatches){
    this.bestMatch = !this.bestMatch;
    if (calculateBestMatches){
      this.reloadMatchScores();
    }
  }

  reloadMatchScores(){
    for (let fragrance of this.fragrances){
      this.user.getFragranceMatchScore(fragrance);
    }
    this.sortByClosestMatches();
  }

  getNextFragrance(): void{
    let ranked = true;
    while (ranked){
      this.currentFragrance = this.displayArr.shift();
      ranked = this.currentFragrance.ranked;
    }
  
    if (this.displayArr.length < 5){
      this.reloadMatchScores();
      const shuffled = [...this.fragrances].sort(() => 0.5 - Math.random());
      this.displayArr = this.displayArr.concat(shuffled.slice(0, 5));
    }
  }

  goodFit(fragrance: Fragrance){
    this.user.rankFragrance(2, fragrance);
    fragrance.ranked = true;
  }

  badFit(fragrance: Fragrance){
    this.user.rankFragrance(-2, fragrance);
    fragrance.ranked = true;
  }

  getBestMatches(){
    this.fragrances.sort(function(a, b){
      if(a.score > b.score) { return -1; }
      if(a.score < b.score) { return 1; }
      return 0;
    });
    let comps = [...this.fragrances].filter(elem => elem.score != NaN);
    return comps.slice(0, 10);
  }

  printUserData(){
    console.log(this.user)
  }

  addToFavorites(match: Fragrance){
    this.user.addFragranceToFavorites(match);
  }

  printMatchInfo(match: Fragrance){
    let results: number[] = [];
    let userArr: number[] = [];
    let rankedMap = match.getRankedMap();
    for (let key of rankedMap.keys()){
        if (this.user.preferences.get(key)){
            userArr.push(this.user.normalizeScore(this.user.preferences.get(key)));
        } else {
            userArr.push(0);
        }
        results.push((rankedMap.get(key) / 2));
    }

    console.log(userArr)
    console.log(results)
    console.log(match)
  }

  rankFragrance(rank: number): void{
    rank = rank - 2;
    this.user.rankFragrance(rank, this.currentFragrance);
    console.log(this.currentFragrance, this.user.preferences)
    this.currentFragrance.ranked = true;
    this.currentFragrance.rank = rank;
    this.getNextFragrance();
  }

  favoriteFragrance(): void{
    this.user.addFragranceToFavorites(this.currentFragrance);
  }
  
  canSeeMatches(){
    return this.user.preferences && Array.from(this.user.preferences.keys()).length > 0
  }

  getMatchValue(match: Fragrance){
    return Math.round((this.user.getFragranceMatchScore(match)) * 100);
  }
}