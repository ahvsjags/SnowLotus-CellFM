test_that("bundle reader exposes core Agent artifacts", {
  root <- file.path(tempdir(), "plantcellfm-test-bundle")
  dir.create(root, recursive = TRUE, showWarnings = FALSE)
  writeLines('{"status":"passed"}', file.path(root, "evidence_verification.json"))
  writeLines('{"route":"universal_open_set"}', file.path(root, "route_decision.json"))
  writeLines(c("cell_id,fine_label,fine_confidence,coarse_label,coarse_confidence",
               "c1,xylem,0.9,xylem,0.8"), file.path(root, "predictions.csv"))
  writeLines(c("review_reason\tcell_id\tfine_label", "low_confidence\tc1\txylem"),
             file.path(root, "uncertainty_review.tsv"))
  bundle <- plantcellfm_read_bundle(root)
  expect_s3_class(bundle, "plantcellfm_bundle")
  expect_equal(nrow(bundle$predictions), 1)
  expect_equal(bundle$verification$status, "passed")
  expect_equal(bundle$route$route, "universal_open_set")
  expect_equal(bundle$review$cell_id, "c1")
})

test_that("installation check returns structured status", {
  result <- plantcellfm_check_installation(python = "definitely-not-a-python", project_root = tempdir())
  expect_false(result$ok)
})
