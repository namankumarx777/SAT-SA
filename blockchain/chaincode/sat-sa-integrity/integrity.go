package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
)

// IntegrityContract provides methods for managing SENTRA cryptographic evidence commitments.
type IntegrityContract struct {
	contractapi.Contract
}

// RecordType defines the type of integrity record stored on the ledger.
type RecordType string

const (
	RecordTypeSubmission RecordType = "SUBMISSION"
	RecordTypeFinding    RecordType = "FINDING"
	RecordTypeEvidence   RecordType = "EVIDENCE"
)

// VerificationStatus defines result states for cryptographic verification against the ledger.
type VerificationStatus string

const (
	StatusVerified VerificationStatus = "VERIFIED"
	StatusMismatch VerificationStatus = "MISMATCH"
	StatusNotFound VerificationStatus = "NOT_FOUND"
)

// SubmissionRecord represents an on-chain commitment for a CSE quarterly/periodic submission.
type SubmissionRecord struct {
	RecordID     string     `json:"recordId"`
	RecordType   RecordType `json:"recordType"`
	EntityID     string     `json:"entityId"`
	Period       string     `json:"period"`
	ContentHash  string     `json:"contentHash"`
	ManifestHash string     `json:"manifestHash"`
	CreatedAt    string     `json:"createdAt"`
	RegisteredBy string     `json:"registeredBy"`
	Version      int        `json:"version"`
}

// FindingRecord represents an on-chain commitment for an analytical finding.
type FindingRecord struct {
	RecordID     string     `json:"recordId"`
	RecordType   RecordType `json:"recordType"`
	EntityID     string     `json:"entityId"`
	FindingHash  string     `json:"findingHash"`
	SourcePhase  string     `json:"sourcePhase"`
	DetectorID   string     `json:"detectorId"`
	CreatedAt    string     `json:"createdAt"`
	RegisteredBy string     `json:"registeredBy"`
	Version      int        `json:"version"`
}

// EvidenceRecord represents an on-chain commitment for a specific evidence item supporting a finding.
type EvidenceRecord struct {
	RecordID     string     `json:"recordId"`
	RecordType   RecordType `json:"recordType"`
	EntityID     string     `json:"entityId"`
	FindingID    string     `json:"findingId"`
	ContentHash  string     `json:"contentHash"`
	CreatedAt    string     `json:"createdAt"`
	RegisteredBy string     `json:"registeredBy"`
	Version      int        `json:"version"`
}

// GenericRecord allows unified inspection and hashing verification across record types.
type GenericRecord struct {
	RecordID     string     `json:"recordId"`
	RecordType   RecordType `json:"recordType"`
	EntityID     string     `json:"entityId"`
	ContentHash  string     `json:"contentHash,omitempty"`
	FindingHash  string     `json:"findingHash,omitempty"`
	ManifestHash string     `json:"manifestHash,omitempty"`
	FindingID    string     `json:"findingId,omitempty"`
	SourcePhase  string     `json:"sourcePhase,omitempty"`
	DetectorID   string     `json:"detectorId,omitempty"`
	Period       string     `json:"period,omitempty"`
	CreatedAt    string     `json:"createdAt"`
	RegisteredBy string     `json:"registeredBy"`
	Version      int        `json:"version"`
}

// VerificationResult holds the result of a ledger verification query.
type VerificationResult struct {
	RecordID     string             `json:"recordId"`
	Status       VerificationStatus `json:"status"`
	ExpectedHash string             `json:"expectedHash"`
	LedgerHash   string             `json:"ledgerHash"`
	RecordType   RecordType         `json:"recordType"`
	EntityID     string             `json:"entityId"`
	Version      int                `json:"version"`
	Timestamp    string             `json:"timestamp"`
	Message      string             `json:"message"`
}

// HistoryEntry encapsulates a historical ledger modification.
type HistoryEntry struct {
	TxID      string         `json:"txId"`
	Timestamp string         `json:"timestamp"`
	IsDelete  bool           `json:"isDelete"`
	Record    *GenericRecord `json:"record"`
}

// RegisterSubmission records a new or versioned submission commitment on the ledger.
func (c *IntegrityContract) RegisterSubmission(
	ctx contractapi.TransactionContextInterface,
	recordID string,
	entityID string,
	period string,
	contentHash string,
	manifestHash string,
	timestamp string,
) (*SubmissionRecord, error) {
	if recordID == "" || entityID == "" || contentHash == "" {
		return nil, fmt.Errorf("recordID, entityID, and contentHash are required")
	}

	version := 1
	existingBytes, err := ctx.GetStub().GetState(recordID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if existingBytes != nil {
		var prev GenericRecord
		if err := json.Unmarshal(existingBytes, &prev); err == nil && prev.Version > 0 {
			version = prev.Version + 1
		}
	}

	if timestamp == "" {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	record := SubmissionRecord{
		RecordID:     recordID,
		RecordType:   RecordTypeSubmission,
		EntityID:     entityID,
		Period:       period,
		ContentHash:  contentHash,
		ManifestHash: manifestHash,
		CreatedAt:    timestamp,
		RegisteredBy: "SENTRA",
		Version:      version,
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}

	if err := ctx.GetStub().PutState(recordID, recordJSON); err != nil {
		return nil, fmt.Errorf("failed to put state: %v", err)
	}

	return &record, nil
}

// RegisterFinding records a finding commitment on the ledger.
func (c *IntegrityContract) RegisterFinding(
	ctx contractapi.TransactionContextInterface,
	findingID string,
	entityID string,
	findingHash string,
	sourcePhase string,
	detectorID string,
	timestamp string,
) (*FindingRecord, error) {
	if findingID == "" || entityID == "" || findingHash == "" {
		return nil, fmt.Errorf("findingID, entityID, and findingHash are required")
	}

	version := 1
	existingBytes, err := ctx.GetStub().GetState(findingID)
	if err != nil {
		return nil, fmt.Errorf("failed to read state: %v", err)
	}
	if existingBytes != nil {
		var prev GenericRecord
		if err := json.Unmarshal(existingBytes, &prev); err == nil && prev.Version > 0 {
			version = prev.Version + 1
		}
	}

	if timestamp == "" {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	record := FindingRecord{
		RecordID:     findingID,
		RecordType:   RecordTypeFinding,
		EntityID:     entityID,
		FindingHash:  findingHash,
		SourcePhase:  sourcePhase,
		DetectorID:   detectorID,
		CreatedAt:    timestamp,
		RegisteredBy: "SENTRA",
		Version:      version,
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}

	if err := ctx.GetStub().PutState(findingID, recordJSON); err != nil {
		return nil, fmt.Errorf("failed to put state: %v", err)
	}

	return &record, nil
}

// RegisterEvidence records an evidence item commitment on the ledger.
func (c *IntegrityContract) RegisterEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
	findingID string,
	entityID string,
	evidenceHash string,
	timestamp string,
) (*EvidenceRecord, error) {
	if evidenceID == "" || findingID == "" || evidenceHash == "" {
		return nil, fmt.Errorf("evidenceID, findingID, and evidenceHash are required")
	}

	version := 1
	existingBytes, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to read state: %v", err)
	}
	if existingBytes != nil {
		var prev GenericRecord
		if err := json.Unmarshal(existingBytes, &prev); err == nil && prev.Version > 0 {
			version = prev.Version + 1
		}
	}

	if timestamp == "" {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}

	record := EvidenceRecord{
		RecordID:     evidenceID,
		RecordType:   RecordTypeEvidence,
		EntityID:     entityID,
		FindingID:    findingID,
		ContentHash:  evidenceHash,
		CreatedAt:    timestamp,
		RegisteredBy: "SENTRA",
		Version:      version,
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}

	if err := ctx.GetStub().PutState(evidenceID, recordJSON); err != nil {
		return nil, fmt.Errorf("failed to put state: %v", err)
	}

	return &record, nil
}

// GetRecord returns a stored integrity record from ledger world state.
func (c *IntegrityContract) GetRecord(
	ctx contractapi.TransactionContextInterface,
	recordID string,
) (*GenericRecord, error) {
	recordBytes, err := ctx.GetStub().GetState(recordID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if recordBytes == nil {
		return nil, fmt.Errorf("record %s does not exist on ledger", recordID)
	}

	var record GenericRecord
	if err := json.Unmarshal(recordBytes, &record); err != nil {
		return nil, fmt.Errorf("failed to unmarshal ledger record: %v", err)
	}

	return &record, nil
}

// VerifyRecord compares an expected SHA-256 digest against the on-chain commitment.
func (c *IntegrityContract) VerifyRecord(
	ctx contractapi.TransactionContextInterface,
	recordID string,
	expectedHash string,
) (*VerificationResult, error) {
	recordBytes, err := ctx.GetStub().GetState(recordID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if recordBytes == nil {
		return &VerificationResult{
			RecordID:     recordID,
			Status:       StatusNotFound,
			ExpectedHash: expectedHash,
			LedgerHash:   "",
			Message:      "Record not registered on ledger",
		}, nil
	}

	var record GenericRecord
	if err := json.Unmarshal(recordBytes, &record); err != nil {
		return nil, fmt.Errorf("failed to parse ledger record: %v", err)
	}

	ledgerHash := record.ContentHash
	if ledgerHash == "" {
		ledgerHash = record.FindingHash
	}

	status := StatusMismatch
	message := "Local content hash does NOT match ledger commitment (tamper detected)"
	if expectedHash == ledgerHash {
		status = StatusVerified
		message = "Local content hash matches on-chain cryptographic commitment"
	}

	return &VerificationResult{
		RecordID:     recordID,
		Status:       status,
		ExpectedHash: expectedHash,
		LedgerHash:   ledgerHash,
		RecordType:   record.RecordType,
		EntityID:     record.EntityID,
		Version:      record.Version,
		Timestamp:    record.CreatedAt,
		Message:      message,
	}, nil
}

// GetHistory retrieves the full audit trail of updates and versions for a record.
func (c *IntegrityContract) GetHistory(
	ctx contractapi.TransactionContextInterface,
	recordID string,
) ([]HistoryEntry, error) {
	iterator, err := ctx.GetStub().GetHistoryForKey(recordID)
	if err != nil {
		return nil, fmt.Errorf("failed to get history for key %s: %v", recordID, err)
	}
	defer iterator.Close()

	var history []HistoryEntry
	for iterator.HasNext() {
		modification, err := iterator.Next()
		if err != nil {
			return nil, err
		}

		var record *GenericRecord
		if len(modification.Value) > 0 {
			var r GenericRecord
			if err := json.Unmarshal(modification.Value, &r); err == nil {
				record = &r
			}
		}

		timestamp := ""
		if modification.Timestamp != nil {
			timestamp = modification.Timestamp.AsTime().UTC().Format(time.RFC3339)
		}

		history = append(history, HistoryEntry{
			TxID:      modification.TxId,
			Timestamp: timestamp,
			IsDelete:  modification.IsDelete,
			Record:    record,
		})
	}

	return history, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&IntegrityContract{})
	if err != nil {
		fmt.Printf("Error creating SENTRA-integrity chaincode: %s\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting SENTRA-integrity chaincode: %s\n", err)
	}
}
