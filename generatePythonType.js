const fs = require('fs')

const toPythonType = (type) => {
    switch (typeof type) {
        case 'number':
            return 'float'
        case 'string':
            return 'str'
        case 'boolean':
            return 'bool'
        case 'object':
            if (Array.isArray(type)) {
                return 'list'
            }
            return 'dict'
        default:
            return 'str'
    }
}
const capitalize = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1)
}
const toCamelCase = (str) => {
    return str
        .replaceAll('.', ' ')
        .replaceAll('-', ' ')
        .replaceAll('_', ' ')
        .replaceAll(/[\s]+(.)/g, ($1) => {
            return $1.toUpperCase();
        })
        .replaceAll(/\s/g, '')
        .replace(/^(.)/, ($1) => {
            return $1.toLowerCase();
        });
}


let json = JSON.parse(fs.readFileSync('./sketch文件/.cache/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json', 'utf8'))

let jsonArray = []

const generateArray = (sketch_json) => {
    if (sketch_json.hasOwnProperty('layers')) {
        sketch_json.layers.forEach(layer => {
            generateArray(layer)
        })
    }
    sketch_json['layers'] = []
    sketch_json['userInfo'] = {}
    jsonArray.push(sketch_json)
    return jsonArray
}

let globalInterfaceList = {}

const generateInterfaceKey = (interfaceName) => {
    let interfaceCamelCase = capitalize(toCamelCase(interfaceName))
    let tmpName = interfaceCamelCase
    let i = 1
    while (globalInterfaceList.hasOwnProperty(tmpName)) {
        tmpName = interfaceCamelCase + `_${i++}`
    }
    return tmpName
}

const extractInterfaceFromObjectArray = (interfaceName, objectArray) => {
    let interfaceDict = {}
    globalInterfaceList[interfaceName] = interfaceDict
    if (Array.isArray(objectArray)) {
        let objType = new Set()
        objectArray.forEach(obj => {
            objType.add(typeof obj);
        });
        if (objType.size === 1) {
            let type = Array.from(objType)[0]
            if (type === 'object') {
                objectArray.forEach(obj => {
                    Object.entries(obj).forEach(([key, value]) => {
                        interfaceDict[key] = [toPythonType(value), ...(interfaceDict[key] ?? [])]
                    })
                })
                Object.entries(interfaceDict).forEach(([key, value]) => {
                    let typeSet = new Set(value);
                    if (typeSet.size === 1) {
                        let onlyType = Array.from(typeSet)[0]
                        if (onlyType === 'list' || onlyType === 'dict') {
                            let subObjectArray = objectArray.filter(obj => {
                                return obj.hasOwnProperty(key) && Object.keys(obj[key]).length !== 0
                            }).map(obj => {
                                return obj[key]
                            })
                            let subInterfaceName = generateInterfaceKey(key);
                            if (onlyType === 'list') {
                                subObjectArray = subObjectArray.flat()
                                if (subInterfaceName.endsWith('s')) {
                                    subInterfaceName = subInterfaceName.slice(0, subInterfaceName.indexOf('s'))
                                }
                            }
                            if (subObjectArray.length > 0) {
                                extractInterfaceFromObjectArray(subInterfaceName, subObjectArray)
                                interfaceDict[key] = onlyType === 'list' ? `List[${subInterfaceName}]` : subInterfaceName
                            } else {
                                interfaceDict[key] = onlyType === 'list' ? 'List[Any]' : 'dict'
                            }
                        } else {
                            interfaceDict[key] = onlyType
                        }
                        if (objectArray.length !== value.length) {
                            interfaceDict[key] = `Optional[${interfaceDict[key]}] = None`
                        }
                    } else {
                        interfaceDict[key] = 'Any'
                    }
                })
            } else {
                interfaceDict[interfaceName] = toPythonType(objectArray)
            }
        } else {
            interfaceDict[interfaceName] = 'Any'
        }
    }
    globalInterfaceList[interfaceName] = interfaceDict
    return interfaceDict
}

extractInterfaceFromObjectArray('Layer', generateArray(json))

const mergeInterface = () => {
    Object.entries(globalInterfaceList).forEach(([key, value]) => {
        let basename = key.split('_')[0]
        if (basename !== key && globalInterfaceList.hasOwnProperty(basename)) {
            if (JSON.stringify(globalInterfaceList[basename]) === JSON.stringify(value)) {
                delete globalInterfaceList[key]
                Object.entries(globalInterfaceList).forEach(([kk, vv]) => {
                    Object.entries(vv).forEach(([k, v]) => {
                        globalInterfaceList[kk][k] = v.replace(key, basename)
                    })
                })
            }
        }
    })
}

mergeInterface();
let resultString =
    'from __future__ import annotations\n' +
    'from dataclasses import dataclass, field\n' +
    'from dataclasses_json import DataClassJsonMixin, config\n' +
    'from typing import Any, List, Optional\n' +
    Object.entries(globalInterfaceList).map(([key, value]) => {
        return `@dataclass\nclass ${key}(DataClassJsonMixin):\n` +
            Object.entries(value)
                .sort(([k1, v1], [k2, v2]) => {
                    let v1Optional = v1.includes('Optional')
                    let v2Optional = v2.includes('Optional')
                    if (v1Optional === v2Optional) {
                        return k1.localeCompare(k2);
                    } else {
                        return v1Optional ? 1 : -1;
                    }
                })
                .map(([k, v]) => {
                    return `    ${k}: ${v}\n`.replace(/from\s*:\s*str/g, 'From: str = field(metadata=config(field_name="from"))')
                }).join('')
    }).join('\n') +
    'if __name__ == "__main__":\n' +
    '    json_str = open(\n' +
    '        \'./sketch文件/.cache/洋淘大赏2/pages/ACD24EC7-29B4-4469-834E-04A0331CFDEA.json\', \'r\').read()\n' +
    '    Layer.from_json(json_str)'

fs.writeFileSync('./sketch_type_new.py', resultString)
console.log(resultString)