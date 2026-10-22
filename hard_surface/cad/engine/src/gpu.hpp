#pragma once
#include "model.hpp"

json gpu_render(Model& m, const json& p);        // {path, views?, modes?|mode?, res?, objects?}
json gpu_register_ref(const json& p);            // {name, image, view, m_per_px?, origin_px?, threshold?}
json gpu_iou(Model& m, const json& p);           // {refs?, objects?}
json gpu_deviation(Model& m, const json& p);     // {a, b, heatmap?, tol?, views?, res?}
json gpu_info();
