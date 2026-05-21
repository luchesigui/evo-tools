import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import xlsx from "xlsx";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Carrega os IDs a partir do arquivo Excel
function getIdsFromExcel(fileName) {
  const filePath = path.join(__dirname, "..", "data", fileName);
  const workbook = xlsx.readFile(filePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = xlsx.utils.sheet_to_json(worksheet);
  // Suporta tanto 'ID' quanto 'Id' ou 'id' como nome da coluna
  return data.map((row) => row.ID || row.Id || row.id).filter(Boolean);
}

// Lê os IDs já comunicados, se o arquivo existir
function getAlreadyCommunicatedIds() {
  const filePath = path.join(__dirname, "..", "comunicated-ids.txt");
  if (fs.existsSync(filePath)) {
    return fs
      .readFileSync(filePath, "utf-8")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }
  return [];
}

function getIdsToCommunicate(allIds, alreadyCommunicatedIds) {
  return alreadyCommunicatedIds.length
    ? allIds.filter((id) => !alreadyCommunicatedIds.includes(String(id)))
    : allIds;
}

function addToCommunicatedIds(id) {
  fs.appendFileSync(
    path.join(__dirname, "..", "comunicated-ids.txt"),
    id + "\n"
  );
}

function addToNonExistentClients(id) {
  fs.appendFileSync(
    path.join(__dirname, "..", "clientes-inexistentes.txt"),
    id + "\n"
  );
}

function removeCommunicatedIdsFile() {
  const filePath = path.join(__dirname, "..", "comunicated-ids.txt");
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
    console.log("Arquivo comunicated-ids.txt removido após sucesso total.");
  }
}

export {
  addToCommunicatedIds,
  addToNonExistentClients,
  getAlreadyCommunicatedIds,
  getIdsFromExcel,
  getIdsToCommunicate,
  removeCommunicatedIdsFile,
};
