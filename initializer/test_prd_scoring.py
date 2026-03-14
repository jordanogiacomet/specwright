from initializer.ai.prd_scorer import score_prd


with open("output/editorial-platform/PRD.md") as f:
    prd = f.read()


result = score_prd(prd)

print("\nPRD SCORE RESULT\n")

print(result)