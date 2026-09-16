package main

import (
	"testing"

	"github.com/hyperledger/fabric-chaincode-go/v2/pkg/cid"
	"github.com/hyperledger/fabric-chaincode-go/v2/shim"
	"github.com/hyperledger/fabric-contract-api-go/v2/contractapi"
	"github.com/stretchr/testify/assert"
)

// MockStub implements shim.ChaincodeStubInterface for unit testing.
type MockStub struct {
	shim.ChaincodeStubInterface
	state map[string][]byte
}

func (m *MockStub) GetState(key string) ([]byte, error) {
	val, exists := m.state[key]
	if !exists {
		return nil, nil
	}
	return val, nil
}

func (m *MockStub) PutState(key string, value []byte) error {
	m.state[key] = value
	return nil
}

func (m *MockStub) DelState(key string) error {
	delete(m.state, key)
	return nil
}

// TestTxContext embeds TransactionContext to satisfy contractapi.TransactionContextInterface
type TestTxContext struct {
	contractapi.TransactionContext
	stub *MockStub
}

func (c *TestTxContext) GetStub() shim.ChaincodeStubInterface {
	return c.stub
}

func (c *TestTxContext) GetClientIdentity() cid.ClientIdentity {
	return nil
}

func TestRegisterAndVerifySubmission(t *testing.T) {
	contract := new(IntegrityContract)
	stub := &MockStub{state: make(map[string][]byte)}
	ctx := &TestTxContext{stub: stub}

	// Register Submission
	rec, err := contract.RegisterSubmission(
		ctx,
		"SUB-CSE-011-2026-Q2",
		"CSE-011",
		"2026-Q2",
		"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
		"d41d8cd98f00b204e9800998ecf8427e",
		"2026-09-16T10:00:00Z",
	)
	assert.NoError(t, err)
	assert.Equal(t, "SUB-CSE-011-2026-Q2", rec.RecordID)
	assert.Equal(t, 1, rec.Version)
	assert.Equal(t, RecordTypeSubmission, rec.RecordType)

	// Verify - Match
	res, err := contract.VerifyRecord(ctx, "SUB-CSE-011-2026-Q2", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
	assert.NoError(t, err)
	assert.Equal(t, StatusVerified, res.Status)

	// Verify - Mismatch (tampered hash)
	resMismatch, err := contract.VerifyRecord(ctx, "SUB-CSE-011-2026-Q2", "tampered_hash_value_12345")
	assert.NoError(t, err)
	assert.Equal(t, StatusMismatch, resMismatch.Status)

	// Verify - Not Found
	resNotFound, err := contract.VerifyRecord(ctx, "NON_EXISTENT_SUBMISSION", "some_hash")
	assert.NoError(t, err)
	assert.Equal(t, StatusNotFound, resNotFound.Status)
}

func TestRegisterFindingAndEvidence(t *testing.T) {
	contract := new(IntegrityContract)
	stub := &MockStub{state: make(map[string][]byte)}
	ctx := &TestTxContext{stub: stub}

	// Register Finding
	fRec, err := contract.RegisterFinding(
		ctx,
		"F-3e6ce30d9c2a6646",
		"CSE-011",
		"hash_finding_eg002_sample",
		"phase6",
		"EG002",
		"2026-09-16T10:05:00Z",
	)
	assert.NoError(t, err)
	assert.Equal(t, "F-3e6ce30d9c2a6646", fRec.RecordID)
	assert.Equal(t, RecordTypeFinding, fRec.RecordType)
	assert.Equal(t, 1, fRec.Version)

	// Register Evidence
	eRec, err := contract.RegisterEvidence(
		ctx,
		"EVD-011-001",
		"F-3e6ce30d9c2a6646",
		"CSE-011",
		"hash_evidence_sample_987",
		"2026-09-16T10:06:00Z",
	)
	assert.NoError(t, err)
	assert.Equal(t, "EVD-011-001", eRec.RecordID)
	assert.Equal(t, RecordTypeEvidence, eRec.RecordType)

	// Version update
	fRec2, err := contract.RegisterFinding(
		ctx,
		"F-3e6ce30d9c2a6646",
		"CSE-011",
		"hash_finding_eg002_v2",
		"phase6",
		"EG002",
		"2026-09-16T10:10:00Z",
	)
	assert.NoError(t, err)
	assert.Equal(t, 2, fRec2.Version)

	// Read generic record
	gen, err := contract.GetRecord(ctx, "F-3e6ce30d9c2a6646")
	assert.NoError(t, err)
	assert.Equal(t, 2, gen.Version)
	assert.Equal(t, "hash_finding_eg002_v2", gen.FindingHash)
}
