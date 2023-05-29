const fs = require("fs");
const crypto = require("crypto");
const { get } = require("http");

// get first argument
const filePath = process.argv[2];

const data = JSON.parse(fs.readFileSync(filePath, "utf8"));

// hash all text arrays and attribute a symbol to each
// key is hash of the array
const textsSymbolsMap = new Map();
const AVAILABLE_SYMBOLS_SHAPES = ['star', 'diamond', 'semicircle', 'trapezium', 'ellipse', 'isosceles triangle', 'kite', 'dart', 'cloud', 'signal', 'tape', 'double arrow', 'circle split'];
const AVAILABLE_SYMBOLS = ['star', 'diamond', 'semicircle', 'trapezium', 'ellipse', 'isoscelestriangle', 'kite', 'dart', 'cloud', 'signal', 'tape', 'doublearrow', 'circlesplit'];

const methodsSimMap = new Map();
const methodsScoreMap = new Map();

function hashObject(obj) {
    const objString = JSON.stringify(obj);
    const hash = crypto.createHash('sha256');
    hash.update(objString);
    return hash.digest('hex');
}

function getOrSetTextsSymbol(obj) {
    const hash = hashObject(obj);
    if (textsSymbolsMap.has(hash)) {
        return textsSymbolsMap.get(hash);
    } else {
        const symbol = AVAILABLE_SYMBOLS.shift() + "symbol";
        textsSymbolsMap.set(hash, symbol);
        return symbol;
    }
}

function getOrSetMethodSymbol(method, sim) {
    const map = sim ? methodsSimMap : methodsScoreMap;

    if (map.has(method)) {
        return map.get(method);
    } else {
        const num = map.size + 1;
        const symbol = sim ? `$\\bigodot {}_${num}$` : `$y_{\\text{pred-}${num}}$`;
        map.set(method, symbol);
        return symbol;
    }
}

const result = data.map((item) => {
  const textTrue = `% true: [${item.text_true.join(", ")}]`;
  const textFalse = `% false: [${item.text_false.join(", ")}]`;

  let minusSimilarityWeight = "";
  if (item.method.hasOwnProperty("minus_similarity_weight")) {
    minusSimilarityWeight = item.method.minus_similarity_weight.toString();
  }

  const modelInfo = [
    item.model_name,
    getOrSetMethodSymbol(item.method.similarity, true),
    getOrSetMethodSymbol(item.method.y_score, false),
    minusSimilarityWeight,
    `\\${getOrSetTextsSymbol(item.text_true)}{}`,
    `\\${getOrSetTextsSymbol(item.text_false)}{}`,
    item.roc_auc.toString(),
    item.pr_auc.toString(),
    item.TP.toString(),
    item.FN.toString(),
    item.FP.toString(),
    item.TN.toString(),
  ].join(" & ");

  return [textTrue, textFalse, modelInfo].join("\n");
}).join(" \\\\\n\n");


// before printing the results, print the symbols map
//  example: \newcommand*{\greenstar}{\tikz \node[draw=black!60, star, fill=green!50, star points=5, inner sep=2pt] {};}
const symbolMap = Array.from(textsSymbolsMap.values()).map((symbolCommandName, i) => {
    return `\\newcommand*{\\${symbolCommandName}}{\\tikz \\node[draw=black!60, ${AVAILABLE_SYMBOLS_SHAPES[i]}, fill=green!50, inner sep=2pt] {};}`
});
console.log(symbolMap.join('\n'));

console.log('\n\n');
// print the table
console.log(result);
