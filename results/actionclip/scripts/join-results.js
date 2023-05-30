const fs = require("fs");
const crypto = require("crypto");
const chroma = require("chroma-js");

// get first argument
const filePath = process.argv[2];


const data = JSON.parse(fs.readFileSync(filePath, "utf8"));


// hash all text arrays and attribute a symbol to each
// key is hash of the array
const textsSymbolsMap = new Map();

const colors = chroma.scale(['orange', 'indigo', '008ae5', 'lightgreen']).mode('lch').colors(13);

const AVAILABLE_SYMBOLS = [
    {
        index: 1,
        command: 'starResultSymbol',
        properties: `fill=starSymbolColor, star`,
        colorDef: 'starSymbolColor',
        colorHex: colors[0],
    },
    {
        index: 2,
        command: 'diamondResultSymbol',
        properties: `fill=diamondSymbolColor, diamond`,
        colorDef: 'diamondSymbolColor',
        colorHex: colors[1],
    },
    {
        index: 3,
        command: 'semicircleResultSymbol',
        properties: `fill=semicircleSymbolColor, semicircle`,
        colorDef: 'semicircleSymbolColor',
        colorHex: colors[2],
    },
    {
        index: 4,
        command: 'trapeziumResultSymbol',
        properties: `fill=trapeziumSymbolColor, trapezium`,
        colorDef: 'trapeziumSymbolColor',
        colorHex: colors[3],
    },
    {
        index: 5,
        command: 'ellipseResultSymbol',
        properties: `fill=ellipseSymbolColor, ellipse`,
        colorDef: 'ellipseSymbolColor',
        colorHex: colors[4],
    },
    {
        index: 6,
        command: 'isoscelestriangleResultSymbol',
        properties: `fill=isoscelestriangleSymbolColor, isosceles triangle`,
        colorDef: 'isoscelestriangleSymbolColor',
        colorHex: colors[5],
    },
    {
        index: 7,
        command: 'kiteResultSymbol',
        properties: `fill=kiteSymbolColor, kite`,
        colorDef: 'kiteSymbolColor',
        colorHex: colors[6],
    },
    {
        index: 8,
        command: 'dartResultSymbol',
        properties: `fill=dartSymbolColor, dart`,
        colorDef: 'dartSymbolColor',
        colorHex: colors[7],
    },
    {
        index: 9,
        command: 'cloudResultSymbol',
        properties: `fill=cloudSymbolColor, cloud`,
        colorDef: 'cloudSymbolColor',
        colorHex: colors[8],
    },
    {
        index: 10,
        command: 'signalResultSymbol',
        properties: `fill=signalSymbolColor, signal`,
        colorDef: 'signalSymbolColor',
        colorHex: colors[9],
    },
    {
        index: 11,
        command: 'tapeResultSymbol',
        properties: `fill=tapeSymbolColor, tape, minimum width=1.5em, scale=0.6`,
        colorDef: 'tapeSymbolColor',
        colorHex: colors[10],
    },
    {
        index: 12,
        command: 'doublearrowResultSymbol',
        properties: `fill=doublearrowSymbolColor, double arrow, double arrow head extend=0.1cm, minimum height=1.1em, scale=0.7`,
        colorDef: 'doublearrowSymbolColor',
        colorHex: colors[11],
    },
    {
        index: 13,
        command: 'circlesplitResultSymbol',
        properties: `fill=circlesplitSymbolColor, circle split`,
        colorDef: 'circlesplitSymbolColor',
        colorHex: colors[12],
    },
];

if (AVAILABLE_SYMBOLS.length < colors.length) {
    throw new Error("Not enough colors for symbols available");
}

const reversePosTextsSymbolsMap = new Map();
const reverseNegTextsSymbolsMap = new Map();


const methodsSimMap = new Map();
const methodsScoreMap = new Map();

function hashObject(obj) {
    const objString = JSON.stringify(obj);
    const hash = crypto.createHash('sha256');
    hash.update(objString);
    return hash.digest('hex');
}

function getOrSetTextsSymbol(texts, positive) {
    const hash = hashObject(texts);
    if (textsSymbolsMap.has(hash)) {
        return textsSymbolsMap.get(hash);
    } else {
        if (AVAILABLE_SYMBOLS.length === 0) {
            throw new Error("No more symbols available");
        }
        const symbol = AVAILABLE_SYMBOLS.shift();
        textsSymbolsMap.set(hash, symbol);
        if (positive) {
            reversePosTextsSymbolsMap.set(symbol.command, texts);
        } else {
            reverseNegTextsSymbolsMap.set(symbol.command, texts);
        }
        return symbol;
    }
}

function getOrSetMethodSymbol(method, sim) {
    const map = sim ? methodsSimMap : methodsScoreMap;

    if (map.has(method)) {
        return map.get(method);
    } else {
        const num = map.size + 1;
        const symbol = {
            method,
            num,
        };
        map.set(method, symbol);
        return symbol;
    }
}

// init order of texts symbols by pos and then neg
data.map(item => getOrSetTextsSymbol(item.text_true, true));
data.map(item => getOrSetTextsSymbol(item.text_false, false));

// produce rows
const rows = data.map((item) => {
  const textTrue = item.text_true.join(", ");
  const textFalse = item.text_false.join(", ");

  let minusSimilarityWeight = "";
  if (item.method.hasOwnProperty("minus_similarity_weight")) {
    minusSimilarityWeight = item.method.minus_similarity_weight.toFixed(4);
  }

  const modelInfo = {
    trueTexts: textTrue,
    falseTexts: textFalse,
    modelName: item.model_name,
    simiMethod: getOrSetMethodSymbol(item.method.similarity, true).num,
    scoreMethod: getOrSetMethodSymbol(item.method.y_score, false).num,
    methodWeight: minusSimilarityWeight,
    positiveSymbol: getOrSetTextsSymbol(item.text_true, true).command,
    negativeSymbol: getOrSetTextsSymbol(item.text_false, false).command,
    rocAucScore: item.roc_auc.toFixed(3),
    prAucScore: item.pr_auc.toFixed(3),
    TP: item.TP.toString(),
    FN: item.FN.toString(),
    FP: item.FP.toString(),
    TN: item.TN.toString(),
  };

  return modelInfo
})
.sort((a, b) => a.rocAucScore - b.rocAucScore);

const colorsDefinitions = Array.from(textsSymbolsMap.values()).map((symbol) => {
    return {
        colorDef: symbol.colorDef,
        colorHex: symbol.colorHex.substring(1),
    };
});

const symbolsCommands = Array.from(textsSymbolsMap.values()).map((symbol) => {
    return {
        command: symbol.command,
        index: symbol.index,
        properties: symbol.properties,
    };
});

const positiveTextsSymbols = Array.from(reversePosTextsSymbolsMap.entries()).map(([command, texts]) => {
    return {
        command,
        texts: texts.sort((a, b) => a.localeCompare(b)).join(", "),
    };
});

const negativeTextsSymbols = Array.from(reverseNegTextsSymbolsMap.entries()).map(([command, texts]) => {
    return {
        command,
        texts: texts.length === 0
            ? "$\\emptyset$"
            : texts.sort((a, b) => a.localeCompare(b)).join(", ")
    };
});

const simiMethods = Array.from(methodsSimMap.values()).map(({num, method}) => {
    return {
        num, method
    };
});
const scoreMethods = Array.from(methodsScoreMap.values()).map(({num, method}) => {
    return {
        num, method
    };
});

const result = {
    colorsDefinitions,
    symbolsCommands,
    rows,
    positiveTextsSymbols,
    negativeTextsSymbols,
    simiMethods,
    scoreMethods,
};

console.log(JSON.stringify(result, null, 4));

